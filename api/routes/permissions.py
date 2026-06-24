from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api.middleware import get_current_user, require_permission
from modules.permissions.rbac import (
    create_role,
    get_role,
    list_roles,
    create_permission,
    list_permissions,
    assign_role_to_user,
    remove_role_from_user,
    get_user_roles,
    get_user_permissions,
    user_has_permission,
    assign_permission_to_role,
    get_role_permissions,
    seed_default_data,
)
from modules.audit.logger import audit_log

router = APIRouter()


class RoleCreate(BaseModel):
    name: str
    description: str = ""


class PermissionCreate(BaseModel):
    resource: str
    action: str
    description: str = ""


class RoleAssign(BaseModel):
    username: str
    role_id: str


class PermissionAssign(BaseModel):
    role_id: str
    permission_id: str


@router.get("/roles")
async def list_all_roles(username: str = Depends(require_permission("admin", "roles"))):
    return list_roles()


@router.post("/roles")
async def create_new_role(
    req: RoleCreate,
    username: str = Depends(require_permission("admin", "roles")),
):
    return create_role(req.name, req.description)


@router.get("/roles/{role_id}")
async def get_role_by_id(
    role_id: str,
    username: str = Depends(require_permission("admin", "roles")),
):
    role = get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Papel não encontrado")
    return role


@router.get("/roles/{role_id}/permissions")
async def list_role_permissions(
    role_id: str,
    username: str = Depends(require_permission("admin", "roles")),
):
    return get_role_permissions(role_id)


@router.get("/permissions")
async def list_all_permissions(
    username: str = Depends(require_permission("admin", "roles")),
):
    return list_permissions()


@router.post("/permissions")
async def create_new_permission(
    req: PermissionCreate,
    username: str = Depends(require_permission("admin", "roles")),
):
    return create_permission(req.resource, req.action, req.description)


@router.post("/assign")
async def assign_role(
    req: RoleAssign,
    username: str = Depends(require_permission("admin", "roles")),
):
    assign_role_to_user(req.username, req.role_id, granted_by=username)
    audit_log(username, "assign_role", resource="permissions", details=f"{req.username} -> {req.role_id}")
    return {"message": "Papel atribuído com sucesso"}


@router.delete("/assign")
async def unassign_role(
    req: RoleAssign,
    username: str = Depends(require_permission("admin", "roles")),
):
    remove_role_from_user(req.username, req.role_id)
    audit_log(username, "remove_role", resource="permissions", details=f"{req.username} -> {req.role_id}")
    return {"message": "Papel removido com sucesso"}


@router.post("/assign-permission")
async def assign_permission_to_role_route(
    req: PermissionAssign,
    username: str = Depends(require_permission("admin", "roles")),
):
    assign_permission_to_role(req.role_id, req.permission_id)
    return {"message": "Permissão atribuída ao papel"}


@router.get("/users/{target_user}/roles")
async def user_roles(
    target_user: str,
    username: str = Depends(require_permission("admin", "users")),
):
    return get_user_roles(target_user)


@router.get("/users/{target_user}/permissions")
async def user_permissions(
    target_user: str,
    username: str = Depends(require_permission("admin", "users")),
):
    return get_user_permissions(target_user)


@router.get("/check")
async def check_permission(
    resource: str,
    action: str,
    username: str = Depends(get_current_user),
):
    return {"has_permission": user_has_permission(username, resource, action)}


@router.post("/seed")
async def seed_data(username: str = Depends(require_permission("admin", "roles"))):
    seed_default_data()
    return {"message": "Dados default populados"}
