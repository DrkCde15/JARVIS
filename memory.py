import base64
import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from jose import JWTError, jwt  # type: ignore


load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = BASE_DIR / "jarvis.sqlite3"

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
LEGACY_SHA256_HEX_LENGTH = 64
BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")
SMTP_SECRET_PREFIX = "fernet:"

_database_initialized = False


def obter_dias_expiracao_token():
    try:
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "365"))
    except (TypeError, ValueError):
        return 365


ACCESS_TOKEN_EXPIRE_DAYS = obter_dias_expiracao_token()


def obter_caminho_banco_sqlite():
    configured_path = os.getenv("SQLITE_DB_PATH") or os.getenv("JARVIS_DB_PATH")
    if not configured_path:
        return DEFAULT_DATABASE_PATH

    database_path = Path(configured_path).expanduser()
    if database_path.is_absolute():
        return database_path
    return BASE_DIR / database_path


def conectar_sqlite():
    database_path = obter_caminho_banco_sqlite()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        database_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        timeout=30,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def criar_tabelas():
    global _database_initialized

    table_statements = [
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            senha_hash TEXT NOT NULL,
            last_login TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS sessoes (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            is_valid INTEGER DEFAULT 1,
            FOREIGN KEY (username) REFERENCES usuarios(username)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS message_store (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessoes(id)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS logs (
            id TEXT PRIMARY KEY,
            username TEXT,
            acao TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS smtp_credentials (
            username TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            senha_b64 TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES usuarios(username)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_credentials (
            username TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            api_key_secret TEXT NOT NULL,
            model_name TEXT NOT NULL,
            base_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES usuarios(username)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            objective TEXT NOT NULL,
            status TEXT NOT NULL,
            plan_json TEXT,
            result TEXT,
            error TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES usuarios(username)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_steps (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            step_index INTEGER NOT NULL,
            tool_name TEXT NOT NULL,
            tool_args TEXT,
            status TEXT NOT NULL,
            observation TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES agent_tasks(id)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
    ]

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_sessoes_user_valid ON sessoes(username, is_valid)",
        "CREATE INDEX IF NOT EXISTS idx_message_store_session_time ON message_store(session_id, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_agent_tasks_user_status ON agent_tasks(username, status)",
        "CREATE INDEX IF NOT EXISTS idx_agent_steps_task ON agent_steps(task_id, step_index)",
    ]

    conn = conectar_sqlite()
    try:
        for statement in table_statements + index_statements:
            conn.execute(statement)
        conn.commit()
        _database_initialized = True
    finally:
        conn.close()


def garantir_banco_sqlite():
    if not _database_initialized:
        criar_tabelas()


def get_connection():
    garantir_banco_sqlite()
    return conectar_sqlite()


def release_connection(conn):
    if conn:
        conn.close()


def normalizar_placeholders(query: str):
    return query.replace("%s", "?")


def row_to_dict(row):
    return dict(row) if row else None


def executar_query(query, params=None, *, fetch=False, fetchone=False, commit=False):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(normalizar_placeholders(query), params or ())

        if commit:
            conn.commit()
            return True
        if fetchone:
            return row_to_dict(cursor.fetchone())
        if fetch:
            return [dict(row) for row in cursor.fetchall()]
        return True

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro SQLite: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)


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
        "INSERT INTO usuarios (username, senha_hash) VALUES (?, ?)",
        (username, hash_senha(senha)),
        commit=True,
    )
    registrar_log(username, "Usuario criado")


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
        "SELECT senha_hash FROM usuarios WHERE username=? AND is_active=1",
        (username,),
        fetchone=True,
    )

    if not user or not verificar_senha(senha, user["senha_hash"]):
        return None, None

    if senha_precisa_rehash(user["senha_hash"]):
        executar_query(
            "UPDATE usuarios SET senha_hash=? WHERE username=?",
            (hash_senha(senha), username),
            commit=True,
        )

    token = criar_token_acesso(username)
    session_id = criar_sessao(username, token)
    return token, session_id


def criar_sessao(username: str, token: str) -> str:
    session_id = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    executar_query(
        "INSERT INTO sessoes (id, username, token, expires_at) VALUES (?, ?, ?, ?)",
        (session_id, username, token, expires),
        commit=True,
    )
    registrar_log(username, f"Sessao criada {session_id}")
    return session_id


def obter_session_id_por_token(token: str):
    row = executar_query(
        """
        SELECT id FROM sessoes
        WHERE token=? AND is_valid=1 AND expires_at > ?
        """,
        (token, datetime.utcnow()),
        fetchone=True,
    )
    return row["id"] if row else None


def logout_usuario(username: str, token: str):
    executar_query(
        "UPDATE sessoes SET is_valid=0 WHERE username=? AND token=?",
        (username, token),
        commit=True,
    )
    registrar_log(username, "Logout realizado")


def invalidar_sessoes_usuario(username: str):
    executar_query(
        "UPDATE sessoes SET is_valid=0 WHERE username=?",
        (username,),
        commit=True,
    )
    registrar_log(username, "Todas as sessoes invalidadas")


def listar_sessoes_ativas(username: str = None):
    if username:
        return executar_query(
            """
            SELECT id, username, created_at, expires_at
            FROM sessoes
            WHERE username=? AND is_valid=1 AND expires_at > ?
            ORDER BY created_at DESC
            """,
            (username, datetime.utcnow()),
            fetch=True,
        ) or []

    return executar_query(
        """
        SELECT id, username, created_at, expires_at
        FROM sessoes
        WHERE is_valid=1 AND expires_at > ?
        ORDER BY created_at DESC
        """,
        (datetime.utcnow(),),
        fetch=True,
    ) or []


def get_usuario_ativo(token: str):
    username = verificar_token(token)
    if not username:
        return None

    user = executar_query(
        "SELECT username FROM usuarios WHERE username=? AND is_active=1",
        (username,),
        fetchone=True,
    )
    return user["username"] if user else None


def verificar_usuario_existe(username: str):
    row = executar_query(
        "SELECT username FROM usuarios WHERE username=?",
        (username,),
        fetchone=True,
    )
    return row is not None


def atualizar_senha_usuario(username: str, senha_atual: str, nova_senha: str):
    user = executar_query(
        "SELECT senha_hash FROM usuarios WHERE username=?",
        (username,),
        fetchone=True,
    )

    if not user or not verificar_senha(senha_atual, user["senha_hash"]):
        return False

    executar_query(
        "UPDATE usuarios SET senha_hash=? WHERE username=?",
        (hash_senha(nova_senha), username),
        commit=True,
    )
    registrar_log(username, "Senha atualizada")
    return True


def atualizar_username_usuario(username_atual: str, novo_username: str):
    if verificar_usuario_existe(novo_username):
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE usuarios SET username=? WHERE username=?",
            (novo_username, username_atual),
        )
        cursor.execute(
            "UPDATE logs SET username=? WHERE username=?",
            (novo_username, username_atual),
        )
        conn.commit()
        registrar_log(novo_username, f"Username atualizado de {username_atual}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar username: {e}")
        return False

    finally:
        cursor.close()
        release_connection(conn)


def adicionar_mensagem_chat(session_id: str, message: str, msg_type: str):
    executar_query(
        """
        INSERT INTO message_store (id, session_id, message, type)
        VALUES (?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), session_id, message, msg_type),
        commit=True,
    )


def obter_historico_chat(session_id: str, limit: int = 10):
    rows = executar_query(
        """
        SELECT message, type, timestamp
        FROM message_store
        WHERE session_id=?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (session_id, limit),
        fetch=True,
    )
    return list(reversed(rows)) if rows else []


def limpar_memoria(session_id):
    try:
        resultado = executar_query(
            "DELETE FROM message_store WHERE session_id = ?",
            (session_id,),
            commit=True,
        )

        if resultado is not None:
            return "Memoria de curto prazo apagada do SQLite, Senhor."
        return "Nao encontrei registros para esta sessao ou houve um erro no SQLite."

    except Exception as e:
        print(f"Erro SQLite detalhado: {e}")
        return f"Erro ao acessar memoria SQLite: {e}"


def registrar_log(username: str, acao: str):
    executar_query(
        "INSERT INTO logs (id, username, acao) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), username, acao),
        commit=True,
    )


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
        VALUES (?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            email=excluded.email,
            senha_b64=excluded.senha_b64,
            created_at=CURRENT_TIMESTAMP
        """,
        (username, email, senha_b64),
        commit=True,
    )
    registrar_log(username, "Credenciais SMTP salvas/atualizadas")


def obter_senha_smtp(username: str):
    row = executar_query(
        "SELECT email, senha_b64 FROM smtp_credentials WHERE username=?",
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


def salvar_credenciais_ia(
    username: str,
    provider: str,
    api_key: str,
    model_name: str,
    base_url: str | None = None,
):
    api_key_secret = proteger_senha_smtp(api_key)
    executar_query(
        """
        INSERT INTO ai_credentials (username, provider, api_key_secret, model_name, base_url)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            provider=excluded.provider,
            api_key_secret=excluded.api_key_secret,
            model_name=excluded.model_name,
            base_url=excluded.base_url,
            updated_at=CURRENT_TIMESTAMP
        """,
        (username, provider, api_key_secret, model_name, base_url),
        commit=True,
    )
    registrar_log(username, f"Credenciais de IA atualizadas: {provider}/{model_name}")


def obter_credenciais_ia(username: str):
    row = executar_query(
        """
        SELECT provider, api_key_secret, model_name, base_url
        FROM ai_credentials WHERE username=?
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


def criar_tarefa_agente(username: str, objective: str):
    task_id = str(uuid.uuid4())
    executar_query(
        """
        INSERT INTO agent_tasks (id, username, objective, status)
        VALUES (?, ?, ?, ?)
        """,
        (task_id, username, objective, "running"),
        commit=True,
    )
    registrar_log(username, f"Tarefa agente criada: {task_id}")
    return task_id


def atualizar_tarefa_agente(task_id: str, *, status=None, plan_json=None, result=None, error=None):
    campos = []
    params: list[Any] = []

    if status is not None:
        campos.append("status=?")
        params.append(status)
    if plan_json is not None:
        campos.append("plan_json=?")
        params.append(plan_json)
    if result is not None:
        campos.append("result=?")
        params.append(result)
    if error is not None:
        campos.append("error=?")
        params.append(error)

    if not campos:
        return True

    campos.append("updated_at=CURRENT_TIMESTAMP")
    params.append(task_id)
    return executar_query(
        f"UPDATE agent_tasks SET {', '.join(campos)} WHERE id=?",
        tuple(params),
        commit=True,
    )


def registrar_passo_agente(
    task_id: str,
    step_index: int,
    tool_name: str,
    tool_args: str,
    status: str,
    observation: str,
):
    executar_query(
        """
        INSERT INTO agent_steps (id, task_id, step_index, tool_name, tool_args, status, observation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), task_id, step_index, tool_name, tool_args, status, observation),
        commit=True,
    )


def verificar_autenticacao_persistente(token: str) -> bool:
    username = verificar_token(token)
    if not username:
        return False

    sessao = executar_query(
        """
        SELECT id FROM sessoes
        WHERE token=? AND is_valid=1 AND expires_at > ?
        """,
        (token, datetime.utcnow()),
        fetchone=True,
    )
    return sessao is not None


def obter_username_por_token(token: str):
    return verificar_token(token)


def atualizar_last_login(username: str):
    executar_query(
        "UPDATE usuarios SET last_login=? WHERE username=?",
        (datetime.utcnow(), username),
        commit=True,
    )


def limpar_sessoes_expiradas():
    executar_query(
        "UPDATE sessoes SET is_valid=0 WHERE expires_at <= ?",
        (datetime.utcnow(),),
        commit=True,
    )
    registrar_log("sistema", "Sessoes expiradas limpas")


def verificar_sessao_valida(session_id: str) -> bool:
    sessao = executar_query(
        """
        SELECT id FROM sessoes
        WHERE id=? AND is_valid=1 AND expires_at > ?
        """,
        (session_id, datetime.utcnow()),
        fetchone=True,
    )
    return sessao is not None


def obter_todas_sessoes(username: str = None):
    if username:
        return executar_query(
            """
            SELECT id, username, is_valid, created_at, expires_at
            FROM sessoes WHERE username=? ORDER BY created_at DESC
            """,
            (username,),
            fetch=True,
        ) or []

    return executar_query(
        """
        SELECT id, username, is_valid, created_at, expires_at
        FROM sessoes ORDER BY created_at DESC
        """,
        fetch=True,
    ) or []


def obter_informacoes_usuario(username: str):
    return executar_query(
        """
        SELECT username, created_at, last_login, is_active
        FROM usuarios WHERE username=?
        """,
        (username,),
        fetchone=True,
    )


def contar_mensagens_sessao(session_id: str) -> int:
    result = executar_query(
        "SELECT COUNT(*) as count FROM message_store WHERE session_id=?",
        (session_id,),
        fetchone=True,
    )
    return result["count"] if result else 0
