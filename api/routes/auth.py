from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from memory import (
    autenticar_usuario,
    criar_usuario,
    criar_sessao,
    obter_session_id_por_token,
    verificar_usuario_existe,
    get_usuario_ativo,
    logout_usuario,
    verificar_token,
)
from api.middleware import get_current_user
from modules.audit.logger import audit_log

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str
    session_id: str
    username: str


@router.post("/login")
async def login(req: LoginRequest):
    token, session_id = autenticar_usuario(req.username, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    session_id = session_id or obter_session_id_por_token(token) or criar_sessao(req.username, token)
    audit_log(req.username, "login", resource="auth", status="success")
    return TokenResponse(token=token, session_id=session_id, username=req.username)


@router.post("/register")
async def register(req: RegisterRequest):
    if verificar_usuario_existe(req.username):
        raise HTTPException(status_code=409, detail="Usuário já existe")

    criar_usuario(req.username, req.password)
    token, session_id = autenticar_usuario(req.username, req.password)
    if token:
        session_id = session_id or criar_sessao(req.username, token)

    audit_log(req.username, "register", resource="auth", status="success")
    return {"message": "Conta criada com sucesso", "username": req.username}


@router.post("/logout")
async def logout(username: str = None, token: str = None):
    if username and token:
        logout_usuario(username, token)
        audit_log(username, "logout", resource="auth", status="success")
    return {"message": "Sessão encerrada"}


@router.get("/me")
async def me(username: str = None):
    if not username:
        raise HTTPException(status_code=401, detail="Não autenticado")

    info = {
        "username": username,
        "active": True,
        "roles": [],
        "permissions": [],
    }

    try:
        from modules.permissions.rbac import get_user_roles, get_user_permissions

        info["roles"] = [r["name"] for r in get_user_roles(username)]
        info["permissions"] = [
            f"{p['resource']}:{p['action']}" for p in get_user_permissions(username)
        ]
    except Exception:
        pass

    return info


@router.post("/verify-token")
async def verify_token_route(token: str):
    username = verificar_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Token inválido")
    return {"valid": True, "username": username}
