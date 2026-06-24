import os
from typing import Callable, Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from memory import verificar_token, get_usuario_ativo
from modules.permissions.rbac import user_has_permission
from modules.audit.logger import audit_log

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    if credentials is None:
        token = os.getenv("API_TOKEN")
        if token:
            username = verificar_token(token)
            if username:
                return get_usuario_ativo(token) or username
        return None

    token = credentials.credentials
    username = verificar_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    active_user = get_usuario_ativo(token)
    if not active_user:
        raise HTTPException(status_code=401, detail="Usuário inativo ou não encontrado")

    return active_user


def require_permission(resource: str, action: str):
    async def permission_dependency(
        request: Request,
        username: Optional[str] = Depends(get_current_user),
    ):
        if username is None:
            raise HTTPException(status_code=401, detail="Autenticação necessária")

        if not user_has_permission(username, resource, action):
            audit_log(
                username=username,
                action=f"{resource}:{action}",
                resource=resource,
                details=f"Acesso negado via API - {request.method} {request.url.path}",
                ip_address=request.client.host if request.client else None,
                status="denied",
            )
            raise HTTPException(
                status_code=403,
                detail=f"Permissão negada: {action} em {resource}",
            )

        return username

    return permission_dependency


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    if credentials is None:
        return None
    try:
        token = credentials.credentials
        username = verificar_token(token)
        if username:
            return get_usuario_ativo(token) or username
    except Exception:
        pass
    return None
