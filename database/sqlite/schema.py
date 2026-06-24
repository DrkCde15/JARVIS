_database_initialized_new = False


def get_all_table_statements():
    return [
        # --- RBAC: Roles ---
        """
        CREATE TABLE IF NOT EXISTS roles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # --- RBAC: Permissions ---
        """
        CREATE TABLE IF NOT EXISTS permissions (
            id TEXT PRIMARY KEY,
            resource TEXT NOT NULL,
            action TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(resource, action)
        )
        """,
        # --- RBAC: Role-Permission mapping ---
        """
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id TEXT NOT NULL,
            permission_id TEXT NOT NULL,
            PRIMARY KEY (role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
        # --- RBAC: User-Role mapping ---
        """
        CREATE TABLE IF NOT EXISTS user_roles (
            username TEXT NOT NULL,
            role_id TEXT NOT NULL,
            granted_by TEXT,
            granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (username, role_id),
            FOREIGN KEY (username) REFERENCES usuarios(username) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
        # --- Audit: Enhanced audit logs ---
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            username TEXT,
            action TEXT NOT NULL,
            resource TEXT,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            status TEXT DEFAULT 'success',
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # --- Documents ---
        """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            username TEXT NOT NULL,
            department TEXT DEFAULT '',
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            processed INTEGER DEFAULT 0
        )
        """,
        # --- Document chunks for RAG ---
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
        # --- Code Analysis history ---
        """
        CREATE TABLE IF NOT EXISTS code_analysis (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            language TEXT,
            lines INTEGER DEFAULT 0,
            analysis TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES usuarios(username) ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
        # --- Index for code_analysis ---
        # --- Integrations ---
        """
        CREATE TABLE IF NOT EXISTS integrations (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            service TEXT NOT NULL,
            token_secret TEXT NOT NULL,
            url TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES usuarios(username) ON DELETE CASCADE ON UPDATE CASCADE
        )
        """,
    ]


def get_all_index_statements():
    return [
        "CREATE INDEX IF NOT EXISTS idx_user_roles_username ON user_roles(username)",
        "CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(username)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(username)",
        "CREATE INDEX IF NOT EXISTS idx_document_chunks_doc ON document_chunks(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_code_analysis_user ON code_analysis(username)",
        "CREATE INDEX IF NOT EXISTS idx_code_analysis_created ON code_analysis(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_integrations_user ON integrations(username)",
        "CREATE INDEX IF NOT EXISTS idx_integrations_service ON integrations(service)",
    ]


def criar_tabelas():
    from database.sqlite.connection import get_connection

    global _database_initialized_new
    if _database_initialized_new:
        return

    conn = get_connection()
    try:
        for statement in get_all_table_statements() + get_all_index_statements():
            conn.execute(statement)
        conn.commit()
        _database_initialized_new = True
    finally:
        conn.close()


def garantir_banco():
    criar_tabelas()
