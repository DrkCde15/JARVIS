import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATABASE_PATH = str(BASE_DIR / "jarvis.sqlite3")
MEMORY_DB = ":memory:"


def get_database_path():
    configured_path = os.getenv("SQLITE_DB_PATH") or os.getenv("JARVIS_DB_PATH")
    if not configured_path:
        return DEFAULT_DATABASE_PATH

    configured_path = configured_path.strip()

    if configured_path == MEMORY_DB:
        return MEMORY_DB

    db_path = Path(configured_path).expanduser()
    if db_path.is_absolute():
        return str(db_path)
    return str(BASE_DIR / db_path)


def get_connection():
    database_path = get_database_path()

    if database_path != MEMORY_DB:
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        database_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        timeout=30,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    if database_path != MEMORY_DB:
        conn.execute("PRAGMA journal_mode = WAL")

    return conn


def release_connection(conn):
    if conn:
        conn.close()
