import os
import sys
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

_test_db_path = None


@pytest.fixture(scope="session", autouse=True)
def _set_test_db():
    global _test_db_path
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
        _test_db_path = f.name
    os.environ["SQLITE_DB_PATH"] = _test_db_path
    yield
    if _test_db_path and os.path.exists(_test_db_path):
        os.unlink(_test_db_path)
    if _test_db_path and os.path.exists(_test_db_path + "-wal"):
        os.unlink(_test_db_path + "-wal")
    if _test_db_path and os.path.exists(_test_db_path + "-shm"):
        os.unlink(_test_db_path + "-shm")


@pytest.fixture(autouse=True)
def setup_database():
    from memory import criar_tabelas as criar_tabelas_legado
    from database.sqlite.schema import garantir_banco
    from database.sqlite.migrations import run_migrations

    criar_tabelas_legado()
    garantir_banco()
    run_migrations()
    yield
    from database.sqlite.connection import get_connection, release_connection

    conn = get_connection()
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        for t in tables:
            if t["name"] != "sqlite_sequence":
                conn.execute(f"DELETE FROM \"{t['name']}\"")
        conn.commit()
    finally:
        release_connection(conn)


@pytest.fixture
def test_user():
    from memory import criar_usuario

    criar_usuario("testuser", "testpass123")
    return "testuser"


@pytest.fixture
def admin_user():
    from memory import criar_usuario
    from modules.permissions.rbac import get_role_by_name, assign_role_to_user

    criar_usuario("admin", "admin123")
    admin_role = get_role_by_name("admin")
    if admin_role:
        assign_role_to_user("admin", admin_role["id"], granted_by="system")
    return "admin"
