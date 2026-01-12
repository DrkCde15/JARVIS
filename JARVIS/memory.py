import os
import hashlib
import uuid
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pymysql # type: ignore
from pymysql.cursors import DictCursor # type: ignore
from jose import JWTError, jwt  # type: ignore
from queue import Queue

# =====================================================
# CONFIGURAÇÃO INICIAL
# =====================================================

def carregar_config_mysql():
    load_dotenv(override=True)

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

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-now")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30


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
    print("✅ Pool PyMySQL inicializado")


try:
    init_pool()
except Exception as e:
    print(f"❌ Erro MySQL: {e}")
    _connection_pool = None


def get_connection():
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
    ]

    for sql in tabelas:
        executar_query(sql, commit=True)

    print("✅ Tabelas prontas")


if _connection_pool:
    criar_tabelas()


# =====================================================
# AUTH / USUÁRIOS
# =====================================================

def hash_senha(senha: str):
    return hashlib.sha256(senha.encode()).hexdigest()


def criar_usuario(username: str, senha: str):
    executar_query(
        "INSERT INTO usuarios (username, senha_hash) VALUES (%s,%s)",
        (username, hash_senha(senha)),
        commit=True,
    )
    registrar_log(username, "Usuário criado")


def criar_token_acesso(username: str) -> str:
    payload = {
        "sub": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str):
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

    if not user or user["senha_hash"] != hash_senha(senha):
        return None, None

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
    
    if not user or user["senha_hash"] != hash_senha(senha_atual):
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
        print(f"❌ Erro ao atualizar username: {e}")
        return False
        
    finally:
        cursor.close()
        release_connection(conn)


# =====================================================
# CHAT MEMORY
# =====================================================

def adicionar_mensagem_chat(session_id: str, message: str, msg_type: str):
    executar_query(
        """
        INSERT INTO message_store (id, session_id, message, type)
        VALUES (%s,%s,%s,%s)
        """,
        (str(uuid.uuid4()), session_id, message, msg_type),
        commit=True,
    )


def obter_historico_chat(session_id: str, limit: int = 10):
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

def salvar_senha_smtp(username: str, email: str, senha: str):
    senha_b64 = base64.b64encode(senha.encode()).decode()
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
    return row["email"], base64.b64decode(row["senha_b64"]).decode()


# =====================================================
# FUNÇÕES ADICIONAIS
# =====================================================

def verificar_autenticacao_persistente(token: str) -> bool:
    """
    Verificar se a autenticação ainda é válida
    (Função de compatibilidade - pode ser usada pelo main.py)
    """
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
    """Limpar sessões expiradas do banco de dados"""
    executar_query(
        "UPDATE sessoes SET is_valid=FALSE WHERE expires_at <= %s",
        (datetime.utcnow(),),
        commit=True
    )
    registrar_log("sistema", "Sessões expiradas limpas")


def verificar_sessao_valida(session_id: str) -> bool:
    """Verificar se uma sessão é válida"""
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
    """Obter todas as sessões (ativas e inativas)"""
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
    """Obter informações do usuário"""
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
    """Contar número de mensagens em uma sessão"""
    result = executar_query(
        "SELECT COUNT(*) as count FROM message_store WHERE session_id=%s",
        (session_id,),
        fetchone=True
    )
    return result["count"] if result else 0