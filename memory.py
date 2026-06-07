import os
import hashlib
import uuid
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken
import bcrypt
import pymysql # type: ignore
from pymysql.cursors import DictCursor # type: ignore
from jose import JWTError, jwt  # type: ignore
from queue import Queue

# =====================================================
# CONFIGURAÇÃO INICIAL
# =====================================================

load_dotenv(override=True)

def obter_dias_expiracao_token():
    try:
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "365"))
    except (TypeError, ValueError):
        return 365

def carregar_config_mysql():
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "jarvis"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "jarvis_db"),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": False,
    }
    if not config["password"]:
        raise ValueError("❌ MYSQL_PASSWORD não configurado no .env")
    return config

# =====================================================
# JWT
# =====================================================

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = obter_dias_expiracao_token()
LEGACY_SHA256_HEX_LENGTH = 64
BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")
SMTP_SECRET_PREFIX = "fernet:"

# =====================================================
# POOL PyMySQL
# =====================================================
POOL_SIZE = 5
_connection_pool: Queue[pymysql.connections.Connection] | None = None

def init_pool():
    global _connection_pool
    cfg = carregar_config_mysql()
    pool = Queue(maxsize=POOL_SIZE)
    for _ in range(POOL_SIZE):
        conn = pymysql.connect(**cfg)
        pool.put(conn)
    _connection_pool = pool

def garantir_pool_mysql():
    if _connection_pool is None:
        init_pool()
        criar_tabelas()

def get_connection():
    garantir_pool_mysql()
    if _connection_pool is None:
        raise RuntimeError("Pool MySQL não inicializado")
    return _connection_pool.get()

def release_connection(conn):
    if _connection_pool:
        _connection_pool.put(conn)

# =====================================================
# QUERY
# =====================================================

def executar_query(query, params=None, *, fetch=False, fetchone=False, commit=False):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())

        if commit:
            conn.commit()
            return cursor.lastrowid
        if fetchone:
            return cursor.fetchone()
        if fetch:
            return cursor.fetchall()
        return True

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ MySQL error: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

# =====================================================
# TABELAS
# =====================================================

def criar_tabelas():
    tabelas = [
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            username VARCHAR(100) PRIMARY KEY,
            senha_hash VARCHAR(255) NOT NULL,
            last_login DATETIME,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS sessoes (
            id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            token TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            is_valid BOOLEAN DEFAULT TRUE,
            INDEX idx_user_valid (username, is_valid),
            FOREIGN KEY (username) REFERENCES usuarios(username) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS message_store (
            id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            message TEXT NOT NULL,
            type VARCHAR(20) NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session_time (session_id, timestamp),
            FOREIGN KEY (session_id) REFERENCES sessoes(id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS logs (
            id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(100),
            acao TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS smtp_credentials (
            username VARCHAR(100) PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            senha_b64 TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES usuarios(username) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_credentials (
            username VARCHAR(100) PRIMARY KEY,
            provider VARCHAR(50) NOT NULL,
            api_key_secret TEXT NOT NULL,
            model_name VARCHAR(255) NOT NULL,
            base_url VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES usuarios(username) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            objective TEXT NOT NULL,
            status VARCHAR(30) NOT NULL,
            plan_json LONGTEXT,
            result TEXT,
            error TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_agent_tasks_user_status (username, status),
            FOREIGN KEY (username) REFERENCES usuarios(username) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_steps (
            id VARCHAR(36) PRIMARY KEY,
            task_id VARCHAR(36) NOT NULL,
            step_index INT NOT NULL,
            tool_name VARCHAR(100) NOT NULL,
            tool_args LONGTEXT,
            status VARCHAR(30) NOT NULL,
            observation LONGTEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_agent_steps_task (task_id, step_index),
            FOREIGN KEY (task_id) REFERENCES agent_tasks(id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """,
    ]

    for sql in tabelas:
        executar_query(sql, commit=True)
# =====================================================
# AUTH / USUÁRIOS
# =====================================================

def hash_senha(senha: str):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def hash_senha_legado(senha: str):
    return hashlib.sha256(senha.encode()).hexdigest()

def eh_hash_legado(senha_hash: str):
    if len(senha_hash) != LEGACY_SHA256_HEX_LENGTH:
        return False
    return all(char in "0123456789abcdef" for char in senha_hash.lower())

def verificar_senha(senha: str, senha_hash: str):
    if not senha_hash:
        return False
    if eh_hash_legado(senha_hash):
        return hash_senha_legado(senha) == senha_hash
    if not senha_hash.startswith(BCRYPT_PREFIXES):
        return False
    try:
        return bcrypt.checkpw(senha.encode(), senha_hash.encode())
    except (TypeError, ValueError):
        return False

def senha_precisa_rehash(senha_hash: str):
    if not senha_hash or eh_hash_legado(senha_hash):
        return True
    return not senha_hash.startswith(BCRYPT_PREFIXES)

def criar_usuario(username: str, senha: str):
    executar_query(
        "INSERT INTO usuarios (username, senha_hash) VALUES (%s,%s)",
        (username, hash_senha(senha)),
        commit=True,
    )
    registrar_log(username, "Usuário criado")

def criar_token_acesso(username: str) -> str:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY nao configurada no .env")

    payload = {
        "sub": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str):
    if not SECRET_KEY:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def autenticar_usuario(username: str, senha: str):
    user = executar_query(
        "SELECT senha_hash FROM usuarios WHERE username=%s AND is_active=TRUE",
        (username,),
        fetchone=True,
    )

    if not user or not verificar_senha(senha, user["senha_hash"]):
        return None, None

    if senha_precisa_rehash(user["senha_hash"]):
        executar_query(
            "UPDATE usuarios SET senha_hash=%s WHERE username=%s",
            (hash_senha(senha), username),
            commit=True,
        )

    token = criar_token_acesso(username)
    session_id = criar_sessao(username, token)
    return token, session_id

# =====================================================
# SESSÕES
# =====================================================

def criar_sessao(username: str, token: str) -> str:
    session_id = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    executar_query(
        "INSERT INTO sessoes (id, username, token, expires_at) VALUES (%s,%s,%s,%s)",
        (session_id, username, token, expires),
        commit=True,
    )
    registrar_log(username, f"Sessão criada {session_id}")
    return session_id

def obter_session_id_por_token(token: str):
    row = executar_query(
        """
        SELECT id FROM sessoes
        WHERE token=%s AND is_valid=TRUE AND expires_at > %s
        """,
        (token, datetime.utcnow()),
        fetchone=True,
    )
    return row["id"] if row else None

def logout_usuario(username: str, token: str):
    """Invalidar uma sessão específica"""
    executar_query(
        "UPDATE sessoes SET is_valid=FALSE WHERE username=%s AND token=%s",
        (username, token),
        commit=True
    )
    registrar_log(username, "Logout realizado")

def invalidar_sessoes_usuario(username: str):
    """Invalidar todas as sessões de um usuário"""
    executar_query(
        "UPDATE sessoes SET is_valid=FALSE WHERE username=%s",
        (username,),
        commit=True
    )
    registrar_log(username, "Todas as sessões invalidadas")

def listar_sessoes_ativas(username: str = None):
    """Listar sessões ativas, opcionalmente filtrando por usuário"""
    if username:
        rows = executar_query(
            """
            SELECT id, username, created_at, expires_at 
            FROM sessoes 
            WHERE username=%s AND is_valid=TRUE AND expires_at > %s
            ORDER BY created_at DESC
            """,
            (username, datetime.utcnow()),
            fetch=True
        )
    else:
        rows = executar_query(
            """
            SELECT id, username, created_at, expires_at 
            FROM sessoes 
            WHERE is_valid=TRUE AND expires_at > %s
            ORDER BY created_at DESC
            """,
            (datetime.utcnow(),),
            fetch=True
        )
    return rows or []

def get_usuario_ativo(token: str):
    """Obter usuário ativo baseado no token"""
    username = verificar_token(token)
    if not username:
        return None
    
    # Verificar se o usuário ainda está ativo no banco
    user = executar_query(
        "SELECT username FROM usuarios WHERE username=%s AND is_active=TRUE",
        (username,),
        fetchone=True
    )
    return user["username"] if user else None

# =====================================================
# GESTÃO DE USUÁRIOS
# =====================================================

def verificar_usuario_existe(username: str):
    """Verificar se usuário existe"""
    row = executar_query(
        "SELECT username FROM usuarios WHERE username=%s",
        (username,),
        fetchone=True
    )
    return row is not None

def atualizar_senha_usuario(username: str, senha_atual: str, nova_senha: str):
    """Atualizar senha do usuário"""
    user = executar_query(
        "SELECT senha_hash FROM usuarios WHERE username=%s",
        (username,),
        fetchone=True
    )
    
    if not user or not verificar_senha(senha_atual, user["senha_hash"]):
        return False
    
    executar_query(
        "UPDATE usuarios SET senha_hash=%s WHERE username=%s",
        (hash_senha(nova_senha), username),
        commit=True
    )
    registrar_log(username, "Senha atualizada")
    return True

def atualizar_username_usuario(username_atual: str, novo_username: str):
    """Atualizar nome de usuário"""
    # Verificar se novo username já existe
    if verificar_usuario_existe(novo_username):
        return False
    
    # Iniciar transação
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Atualizar tabela usuarios
        cursor.execute(
            "UPDATE usuarios SET username=%s WHERE username=%s",
            (novo_username, username_atual)
        )
        
        # Atualizar tabela sessoes
        cursor.execute(
            "UPDATE sessoes SET username=%s WHERE username=%s",
            (novo_username, username_atual)
        )
        
        # Atualizar tabela logs
        cursor.execute(
            "UPDATE logs SET username=%s WHERE username=%s",
            (novo_username, username_atual)
        )
        
        # Atualizar tabela smtp_credentials
        cursor.execute(
            "UPDATE smtp_credentials SET username=%s WHERE username=%s",
            (novo_username, username_atual)
        )
        conn.commit()
        registrar_log(username_atual, f"Username atualizado para {novo_username}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar username: {e}")
        return False
        
    finally:
        cursor.close()
        release_connection(conn)

# =====================================================
# CHAT MEMORY
# =====================================================

def adicionar_mensagem_chat(session_id: str, message: str, msg_type: str):
    """Adiciona uma nova interação ao banco MySQL."""
    executar_query(
        """
        INSERT INTO message_store (id, session_id, message, type)
        VALUES (%s,%s,%s,%s)
        """,
        (str(uuid.uuid4()), session_id, message, msg_type),
        commit=True,
    )

def obter_historico_chat(session_id: str, limit: int = 10):
    """Recupera as últimas mensagens para contexto da IA."""
    rows = executar_query(
        """
        SELECT message, type, timestamp
        FROM message_store
        WHERE session_id=%s
        ORDER BY timestamp DESC
        LIMIT %s
        """,
        (session_id, limit),
        fetch=True,
    )
    return list(reversed(rows)) if rows else []

def limpar_memoria(session_id):
    """
    Apaga o histórico da tabela message_store no MySQL para a sessão atual.
    """
    try:
        # Removida a verificação estrita de 'verificar_sessao_valida' 
        # para permitir a limpeza mesmo em sessões recém-criadas ou locais.
        
        # Executa a deleção
        resultado = executar_query(
            "DELETE FROM message_store WHERE session_id = %s",
            (session_id,),
            commit=True
        )
        
        # O MySQL retorna True ou o número de linhas, tratamos como sucesso
        if resultado is not None:
            return "✅ Memória de curto prazo apagada dos núcleos MySQL, Senhor."
        else:
            return "⚠️ Senhor, não encontrei registros para esta sessão ou houve um erro no SQL."

    except Exception as e:
        print(f"❌ Erro MySQL detalhado: {e}")
        return f"❌ Erro ao acessar núcleos de memória MySQL: {e}"

# =====================================================
# LOG
# =====================================================

def registrar_log(username: str, acao: str):
    executar_query(
        "INSERT INTO logs (id, username, acao) VALUES (%s,%s,%s)",
        (str(uuid.uuid4()), username, acao),
        commit=True,
    )

# =====================================================
# SMTP
# =====================================================

def criar_cipher_smtp():
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY nao configurada no .env")
    key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
    return Fernet(key)

def proteger_senha_smtp(senha: str):
    token = criar_cipher_smtp().encrypt(senha.encode()).decode()
    return f"{SMTP_SECRET_PREFIX}{token}"

def revelar_senha_smtp(valor_salvo: str):
    if valor_salvo.startswith(SMTP_SECRET_PREFIX):
        token = valor_salvo.removeprefix(SMTP_SECRET_PREFIX)
        try:
            return criar_cipher_smtp().decrypt(token.encode()).decode()
        except InvalidToken:
            return None

    try:
        return base64.b64decode(valor_salvo).decode()
    except (ValueError, UnicodeDecodeError):
        return None

def salvar_senha_smtp(username: str, email: str, senha: str):
    senha_b64 = proteger_senha_smtp(senha)
    executar_query(
        """
        INSERT INTO smtp_credentials (username, email, senha_b64)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE
        email=%s, senha_b64=%s, created_at=CURRENT_TIMESTAMP
        """,
        (username, email, senha_b64, email, senha_b64),
        commit=True,
    )
    registrar_log(username, "Credenciais SMTP salvas/atualizadas")

def obter_senha_smtp(username: str):
    row = executar_query(
        "SELECT email, senha_b64 FROM smtp_credentials WHERE username=%s",
        (username,),
        fetchone=True,
    )
    if not row:
        return None, None

    senha = revelar_senha_smtp(row["senha_b64"])
    if not senha:
        return row["email"], None

    if not row["senha_b64"].startswith(SMTP_SECRET_PREFIX):
        salvar_senha_smtp(username, row["email"], senha)

    return row["email"], senha

# =====================================================
# CREDENCIAIS DE IA
# =====================================================

def salvar_credenciais_ia(username: str, provider: str, api_key: str, model_name: str, base_url: str | None = None):
    api_key_secret = proteger_senha_smtp(api_key)
    executar_query(
        """
        INSERT INTO ai_credentials (username, provider, api_key_secret, model_name, base_url)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
        provider=%s, api_key_secret=%s, model_name=%s, base_url=%s
        """,
        (
            username,
            provider,
            api_key_secret,
            model_name,
            base_url,
            provider,
            api_key_secret,
            model_name,
            base_url,
        ),
        commit=True,
    )
    registrar_log(username, f"Credenciais de IA atualizadas: {provider}/{model_name}")

def obter_credenciais_ia(username: str):
    row = executar_query(
        """
        SELECT provider, api_key_secret, model_name, base_url
        FROM ai_credentials WHERE username=%s
        """,
        (username,),
        fetchone=True,
    )
    if not row:
        return None

    api_key = revelar_senha_smtp(row["api_key_secret"])
    if not api_key:
        return None

    return {
        "provider": row["provider"],
        "api_key": api_key,
        "model_name": row["model_name"],
        "base_url": row["base_url"],
    }

def usuario_tem_credenciais_ia(username: str) -> bool:
    return obter_credenciais_ia(username) is not None

# =====================================================
# AGENT TASKS
# =====================================================

def criar_tarefa_agente(username: str, objective: str):
    task_id = str(uuid.uuid4())
    executar_query(
        """
        INSERT INTO agent_tasks (id, username, objective, status)
        VALUES (%s,%s,%s,%s)
        """,
        (task_id, username, objective, "running"),
        commit=True,
    )
    registrar_log(username, f"Tarefa agente criada: {task_id}")
    return task_id

def atualizar_tarefa_agente(task_id: str, *, status=None, plan_json=None, result=None, error=None):
    campos = []
    params = []

    if status is not None:
        campos.append("status=%s")
        params.append(status)
    if plan_json is not None:
        campos.append("plan_json=%s")
        params.append(plan_json)
    if result is not None:
        campos.append("result=%s")
        params.append(result)
    if error is not None:
        campos.append("error=%s")
        params.append(error)

    if not campos:
        return True

    params.append(task_id)
    return executar_query(
        f"UPDATE agent_tasks SET {', '.join(campos)} WHERE id=%s",
        tuple(params),
        commit=True,
    )

def registrar_passo_agente(task_id: str, step_index: int, tool_name: str, tool_args: str, status: str, observation: str):
    executar_query(
        """
        INSERT INTO agent_steps (id, task_id, step_index, tool_name, tool_args, status, observation)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (str(uuid.uuid4()), task_id, step_index, tool_name, tool_args, status, observation),
        commit=True,
    )

# =====================================================
# FUNÇÕES ADICIONAIS
# =====================================================

def verificar_autenticacao_persistente(token: str) -> bool:
    username = verificar_token(token)
    if not username:
        return False
    
    # Verificar se há uma sessão válida no banco
    sessao = executar_query(
        """
        SELECT id FROM sessoes 
        WHERE token=%s AND is_valid=TRUE AND expires_at > %s
        """,
        (token, datetime.utcnow()),
        fetchone=True
    )
    
    return sessao is not None

def obter_username_por_token(token: str):
    """Obter username a partir do token JWT"""
    return verificar_token(token)

def atualizar_last_login(username: str):
    """Atualizar timestamp do último login"""
    executar_query(
        "UPDATE usuarios SET last_login=%s WHERE username=%s",
        (datetime.utcnow(), username),
        commit=True
    )

def limpar_sessoes_expiradas():
    executar_query(
        "UPDATE sessoes SET is_valid=FALSE WHERE expires_at <= %s",
        (datetime.utcnow(),),
        commit=True
    )
    registrar_log("sistema", "Sessões expiradas limpas")

def verificar_sessao_valida(session_id: str) -> bool:
    sessao = executar_query(
        """
        SELECT id FROM sessoes 
        WHERE id=%s AND is_valid=TRUE AND expires_at > %s
        """,
        (session_id, datetime.utcnow()),
        fetchone=True
    )
    return sessao is not None

def obter_todas_sessoes(username: str = None):
    if username:
        rows = executar_query(
            """
            SELECT id, username, is_valid, created_at, expires_at
            FROM sessoes WHERE username=%s ORDER BY created_at DESC
            """,
            (username,),
            fetch=True
        )
    else:
        rows = executar_query(
            """
            SELECT id, username, is_valid, created_at, expires_at
            FROM sessoes ORDER BY created_at DESC
            """,
            fetch=True
        )
    return rows or []

def obter_informacoes_usuario(username: str):
    user = executar_query(
        """
        SELECT username, created_at, last_login, is_active
        FROM usuarios WHERE username=%s
        """,
        (username,),
        fetchone=True
    )
    return user

def contar_mensagens_sessao(session_id: str) -> int:
    result = executar_query(
        "SELECT COUNT(*) as count FROM message_store WHERE session_id=%s",
        (session_id,),
        fetchone=True
    )
    return result["count"] if result else 0
