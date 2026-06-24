from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api.middleware import get_current_user, require_permission
from integrations.gitlab.client import GitLabClient
from modules.audit.logger import audit_log

router = APIRouter()


class GitLabConfig(BaseModel):
    token: str
    url: str = "https://gitlab.com"


@router.post("/configure")
async def configure_gitlab(
    config: GitLabConfig,
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
                url=excluded.url,
                updated_at=CURRENT_TIMESTAMP
            """,
            (__import__("uuid").uuid4().hex, username, "gitlab", encrypted, config.url),
        )
        conn.commit()
    finally:
        release_connection(conn)

    audit_log(username, "configure_gitlab", resource="integrations", status="success")
    return {"message": "GitLab configurado"}


@router.get("/projects")
async def list_projects(
    username: str = Depends(require_permission("integrations", "gitlab")),
):
    token, url = _get_gitlab_config(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitLab não configurado")

    client = GitLabClient(token=token, url=url)
    try:
        return client.list_projects()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro no GitLab: {str(e)}")


@router.get("/projects/{project_id}")
async def get_project(
    project_id: int,
    username: str = Depends(require_permission("integrations", "gitlab")),
):
    token, url = _get_gitlab_config(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitLab não configurado")

    client = GitLabClient(token=token, url=url)
    try:
        return client.get_project(project_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/projects/{project_id}/commits")
async def list_commits(
    project_id: int,
    branch: str = "main",
    username: str = Depends(require_permission("integrations", "gitlab")),
):
    token, url = _get_gitlab_config(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitLab não configurado")

    client = GitLabClient(token=token, url=url)
    try:
        return client.list_commits(project_id, branch=branch)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/projects/{project_id}/merges")
async def list_merge_requests(
    project_id: int,
    state: str = "opened",
    username: str = Depends(require_permission("integrations", "gitlab")),
):
    token, url = _get_gitlab_config(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitLab não configurado")

    client = GitLabClient(token=token, url=url)
    try:
        return client.list_merge_requests(project_id, state=state)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/projects/{project_id}/pipelines")
async def list_pipelines(
    project_id: int,
    username: str = Depends(require_permission("integrations", "gitlab")),
):
    token, url = _get_gitlab_config(username)
    if not token:
        raise HTTPException(status_code=400, detail="GitLab não configurado")

    client = GitLabClient(token=token, url=url)
    try:
        return client.list_pipelines(project_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


def _get_gitlab_config(username: str):
    from database.sqlite.connection import get_connection, release_connection

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT token_secret, url FROM integrations WHERE username=? AND service=? AND is_active=1",
            (username, "gitlab"),
        ).fetchone()
        if not row:
            return None, None

        from memory import revelar_senha_smtp

        token = revelar_senha_smtp(row["token_secret"])
        return token, row["url"]
    finally:
        release_connection(conn)
