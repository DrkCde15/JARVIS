import uuid
from typing import Optional

from database.sqlite.connection import get_connection, release_connection
from database.sqlite.schema import garantir_banco
from database.sqlite.migrations import run_migrations


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


def create_role(name: str, description: str = "") -> dict:
    garantir_banco()
    role_id = str(uuid.uuid4())
    _executar(
        "INSERT INTO roles (id, name, description) VALUES (?, ?, ?)",
        (role_id, name, description),
        commit=True,
    )
    return {"id": role_id, "name": name, "description": description}


def get_role(role_id: str) -> Optional[dict]:
    garantir_banco()
    return _executar(
        "SELECT id, name, description, created_at FROM roles WHERE id = ?",
        (role_id,),
        fetchone=True,
    )


def get_role_by_name(name: str) -> Optional[dict]:
    garantir_banco()
    return _executar(
        "SELECT id, name, description, created_at FROM roles WHERE name = ?",
        (name,),
        fetchone=True,
    )


def list_roles() -> list[dict]:
    garantir_banco()
    return _executar(
        "SELECT id, name, description, created_at FROM roles ORDER BY name",
        fetch=True,
    ) or []


def create_permission(resource: str, action: str, description: str = "") -> dict:
    garantir_banco()
    perm_id = str(uuid.uuid4())
    _executar(
        "INSERT INTO permissions (id, resource, action, description) VALUES (?, ?, ?, ?)",
        (perm_id, resource, action, description),
        commit=True,
    )
    return {"id": perm_id, "resource": resource, "action": action, "description": description}


def get_permission(permission_id: str) -> Optional[dict]:
    garantir_banco()
    return _executar(
        "SELECT id, resource, action, description, created_at FROM permissions WHERE id = ?",
        (permission_id,),
        fetchone=True,
    )


def list_permissions() -> list[dict]:
    garantir_banco()
    return _executar(
        "SELECT id, resource, action, description, created_at FROM permissions ORDER BY resource, action",
        fetch=True,
    ) or []


def assign_role_to_user(username: str, role_id: str, granted_by: str = "system"):
    garantir_banco()
    _executar(
        "INSERT OR IGNORE INTO user_roles (username, role_id, granted_by) VALUES (?, ?, ?)",
        (username, role_id, granted_by),
        commit=True,
    )


def remove_role_from_user(username: str, role_id: str):
    _executar(
        "DELETE FROM user_roles WHERE username = ? AND role_id = ?",
        (username, role_id),
        commit=True,
    )


def get_user_roles(username: str) -> list[dict]:
    garantir_banco()
    return _executar(
        """
        SELECT r.id, r.name, r.description, ur.granted_at
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.username = ?
        ORDER BY r.name
        """,
        (username,),
        fetch=True,
    ) or []


def get_user_permissions(username: str) -> list[dict]:
    garantir_banco()
    return _executar(
        """
        SELECT DISTINCT p.resource, p.action, p.description
        FROM user_roles ur
        JOIN role_permissions rp ON rp.role_id = ur.role_id
        JOIN permissions p ON p.id = rp.permission_id
        WHERE ur.username = ?
        ORDER BY p.resource, p.action
        """,
        (username,),
        fetch=True,
    ) or []


def user_has_permission(username: str, resource: str, action: str) -> bool:
    result = _executar(
        """
        SELECT COUNT(*) as count
        FROM user_roles ur
        JOIN role_permissions rp ON rp.role_id = ur.role_id
        JOIN permissions p ON p.id = rp.permission_id
        WHERE ur.username = ? AND p.resource = ? AND p.action = ?
        """,
        (username, resource, action),
        fetchone=True,
    )
    return result["count"] > 0 if result else False


def require_permission(username: str, resource: str, action: str) -> bool:
    if not username:
        return False
    return user_has_permission(username, resource, action)


def assign_permission_to_role(role_id: str, permission_id: str):
    _executar(
        "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
        (role_id, permission_id),
        commit=True,
    )


def get_role_permissions(role_id: str) -> list[dict]:
    return _executar(
        """
        SELECT p.id, p.resource, p.action, p.description
        FROM role_permissions rp
        JOIN permissions p ON p.id = rp.permission_id
        WHERE rp.role_id = ?
        ORDER BY p.resource, p.action
        """,
        (role_id,),
        fetch=True,
    ) or []


def seed_default_data():
    garantir_banco()
    run_migrations()
