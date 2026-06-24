import uuid
from datetime import datetime

from database.sqlite.connection import get_connection, release_connection


def _migrate_documents_department(conn):
    try:
        conn.execute("ALTER TABLE documents ADD COLUMN department TEXT DEFAULT ''")
    except Exception:
        pass


def _migrate_code_analysis(conn):
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS code_analysis (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                language TEXT,
                lines INTEGER DEFAULT 0,
                analysis TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_code_analysis_user ON code_analysis(username)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_code_analysis_created ON code_analysis(created_at)")
    except Exception:
        pass


def run_migrations():
    conn = get_connection()
    try:
        _migrate_documents_department(conn)
        _seed_roles(conn)
        _seed_permissions(conn)
        _assign_default_admin(conn)
        conn.commit()
    finally:
        release_connection(conn)


def _seed_roles(conn):
    existing = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    if existing > 0:
        return

    roles = [
        ("admin", "Administrador com acesso total ao sistema"),
        ("tech", "Acesso a ferramentas técnicas e desenvolvimento"),
        ("security", "Acesso a módulos de segurança e auditoria"),
        ("marketing", "Acesso a documentos e relatórios de marketing"),
        ("finance", "Acesso a relatórios financeiros"),
        ("legal", "Acesso a documentos legais e contratos"),
        ("rh", "Acesso a módulos de recursos humanos"),
        ("user", "Usuário padrão com permissões básicas"),
    ]

    for role_id, (name, desc) in enumerate(roles):
        conn.execute(
            "INSERT OR IGNORE INTO roles (id, name, description) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), name, desc),
        )


def _seed_permissions(conn):
    existing = conn.execute("SELECT COUNT(*) FROM permissions").fetchone()[0]
    if existing > 0:
        return

    permissions = [
        ("chat", "send", "Enviar mensagens no chat"),
        ("chat", "read", "Ler histórico do chat"),
        ("agent", "execute", "Executar agente autônomo"),
        ("tools", "list", "Listar ferramentas disponíveis"),
        ("tools", "use", "Usar ferramentas do sistema"),
        ("files", "read", "Ler arquivos"),
        ("files", "write", "Criar/modificar arquivos"),
        ("files", "delete", "Deletar arquivos"),
        ("admin", "users", "Gerenciar usuários"),
        ("admin", "roles", "Gerenciar papéis e permissões"),
        ("admin", "audit", "Visualizar logs de auditoria"),
        ("documents", "upload", "Fazer upload de documentos"),
        ("documents", "read", "Ler documentos"),
        ("documents", "generate", "Gerar documentos"),
        ("documents", "delete", "Deletar documentos"),
        ("rag", "search", "Buscar na base de conhecimento"),
        ("rag", "index", "Indexar documentos"),
        ("integrations", "github", "Acessar integração GitHub"),
        ("integrations", "gitlab", "Acessar integração GitLab"),
        ("integrations", "configure", "Configurar integrações"),
        ("system", "update", "Atualizar sistema"),
        ("system", "config", "Modificar configurações"),
    ]

    for resource, action, desc in permissions:
        conn.execute(
            "INSERT OR IGNORE INTO permissions (id, resource, action, description) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), resource, action, desc),
        )


def _assign_default_admin(conn):
    from database.sqlite.connection import get_database_path
    from pathlib import Path

    db_path = get_database_path()
    if db_path == ":memory:":
        return
    if not Path(db_path).exists():
        return

    admin_role = conn.execute(
        "SELECT id FROM roles WHERE name = ?", ("admin",)
    ).fetchone()
    if not admin_role:
        return

    usuarios_exist = conn.execute(
        "SELECT COUNT(*) FROM usuarios WHERE 1=1"
    ).fetchone()[0]
    if usuarios_exist == 0:
        return

    existing_assignments = conn.execute(
        "SELECT COUNT(*) FROM user_roles"
    ).fetchone()[0]
    if existing_assignments > 0:
        return

    first_user = conn.execute(
        "SELECT username FROM usuarios ORDER BY created_at ASC LIMIT 1"
    ).fetchone()
    if first_user:
        conn.execute(
            "INSERT OR IGNORE INTO user_roles (username, role_id, granted_by) VALUES (?, ?, ?)",
            (first_user["username"], admin_role["id"], "system"),
        )
