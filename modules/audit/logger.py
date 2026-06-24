import uuid
from datetime import datetime, timedelta
from typing import Optional

from database.sqlite.connection import get_connection, release_connection


def _executar(query, params=None, *, fetch=False, fetchone=False, commit=False):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        if commit:
            conn.commit()
            return True
        if fetchone:
            row = cursor.fetchone()
            return dict(row) if row else None
        if fetch:
            return [dict(r) for r in cursor.fetchall()]
        return True
    finally:
        release_connection(conn)


def audit_log(
    username: str,
    action: str,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    status: str = "success",
):
    log_id = str(uuid.uuid4())
    _executar(
        """
        INSERT INTO audit_logs (id, username, action, resource, resource_id, details, ip_address, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (log_id, username, action, resource, resource_id, details, ip_address, status),
        commit=True,
    )


def get_audit_logs(
    username: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    conditions = []
    params = []

    if username:
        conditions.append("username = ?")
        params.append(username)
    if action:
        conditions.append("action LIKE ?")
        params.append(f"%{action}%")
    if resource:
        conditions.append("resource = ?")
        params.append(resource)
    if status:
        conditions.append("status = ?")
        params.append(status)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    return _executar(
        f"""
        SELECT id, username, action, resource, resource_id, details, ip_address, status, timestamp
        FROM audit_logs
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
        """,
        tuple(params + [limit, offset]),
        fetch=True,
    ) or []


def clean_old_logs(days: int = 90):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    _executar(
        "DELETE FROM audit_logs WHERE timestamp < ?",
        (cutoff,),
        commit=True,
    )
