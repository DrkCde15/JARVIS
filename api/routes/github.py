from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api.middleware import get_current_user, require_permission
from integrations.github.client import GitHubClient
from modules.audit.logger import audit_log

router = APIRouter()


class GitHubConfig(BaseModel):
    token: str


@router.post("/configure")
async def configure_github(
    config: GitHubConfig,
    username: str = Depends(require_permission("integrations", "configure")),
):
    from database.sqlite.connection import get_connection, release_connection

    from memory import proteger_senha_smtp

    conn = get_connection()
    try:
        encrypted = proteger_senha_smtp(config.token)
        conn.execute(
            """
            INSERT INTO integrations (id, username, service, token_secret, url)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username, service) DO UPDATE SET
                token_secret=excluded.token_secret,
                updated_at=CURRENT_TIMESTAMP
            """,
            (__import__("uuid").uuid4().hex, username, "github", encrypted, "https://github.com"),
        )
        conn.commit()
    finally:
        release_connection(conn)

    audit_log(username, "configure_github", resource="integrations", status="success")
    return {"message": "GitHub configurado"}


@router.get("/repos")
async def list_repos(
    username: str = Depends(require_permission("integrations", "github")),
):
    from memory import obter_credenciais_ia

    token = _get_github_token(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub não configurado")

    client = GitHubClient(token=token)
    try:
        return client.list_repos()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro no GitHub: {str(e)}")


@router.get("/repos/{owner}/{repo}")
async def get_repo(
    owner: str,
    repo: str,
    username: str = Depends(require_permission("integrations", "github")),
):
    token = _get_github_token(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub não configurado")

    client = GitHubClient(token=token)
    try:
        return client.get_repo(f"{owner}/{repo}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/repos/{owner}/{repo}/commits")
async def list_commits(
    owner: str,
    repo: str,
    branch: str = "main",
    username: str = Depends(require_permission("integrations", "github")),
):
    token = _get_github_token(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub não configurado")

    client = GitHubClient(token=token)
    try:
        return client.list_commits(f"{owner}/{repo}", branch=branch)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/repos/{owner}/{repo}/pulls")
async def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    username: str = Depends(require_permission("integrations", "github")),
):
    token = _get_github_token(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub não configurado")

    client = GitHubClient(token=token)
    try:
        return client.list_pull_requests(f"{owner}/{repo}", state=state)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/repos/{owner}/{repo}/diff/{pr_number}")
async def get_diff_summary(
    owner: str,
    repo: str,
    pr_number: int,
    username: str = Depends(require_permission("integrations", "github")),
):
    token = _get_github_token(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub não configurado")

    client = GitHubClient(token=token)
    try:
        return {"summary": client.get_diff_summary(f"{owner}/{repo}", pr_number)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


def _get_github_token(username: str) -> Optional[str]:
    from database.sqlite.connection import get_connection, release_connection

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT token_secret FROM integrations WHERE username=? AND service=? AND is_active=1",
            (username, "github"),
        ).fetchone()
        if not row:
            return None

        from memory import revelar_senha_smtp

        return revelar_senha_smtp(row["token_secret"])
    finally:
        release_connection(conn)
