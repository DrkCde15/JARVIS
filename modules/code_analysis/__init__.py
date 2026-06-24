import uuid
from pathlib import Path
from typing import Optional
from database.sqlite.connection import get_connection, release_connection


def salvar_analise(
    username: str,
    filename: str,
    file_path: str,
    language: str,
    lines: int,
    analysis: str,
):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO code_analysis (id, username, filename, file_path, language, lines, analysis)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), username, filename, file_path, language, lines, analysis),
        )
        conn.commit()
    finally:
        release_connection(conn)


def listar_analises(username: Optional[str] = None, limit: int = 20) -> list[dict]:
    conn = get_connection()
    try:
        if username:
            rows = conn.execute(
                """SELECT id, username, filename, language, lines, created_at
                   FROM code_analysis WHERE username = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (username, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, username, filename, language, lines, created_at
                   FROM code_analysis ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        release_connection(conn)


def obter_analise(analysis_id: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM code_analysis WHERE id = ?", (analysis_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        release_connection(conn)
