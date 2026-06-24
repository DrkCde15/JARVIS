from fastapi import APIRouter

from api.routes.auth import router as auth_router
from api.routes.permissions import router as permissions_router
from api.routes.rag import router as rag_router
from api.routes.documents import router as documents_router
from api.routes.github import router as github_router
from api.routes.gitlab import router as gitlab_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Autenticação"])
router.include_router(permissions_router, prefix="/permissions", tags=["Permissões"])
router.include_router(rag_router, prefix="/rag", tags=["RAG - Busca Semântica"])
router.include_router(documents_router, prefix="/documents", tags=["Geração de Documentos"])
router.include_router(github_router, prefix="/github", tags=["Integração GitHub"])
router.include_router(gitlab_router, prefix="/gitlab", tags=["Integração GitLab"])


@router.get("/routes")
async def list_routes():
    return {"message": "JARVIS API v3.0 - Rotas disponíveis em /docs"}
