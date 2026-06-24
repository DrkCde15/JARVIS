import os
from typing import Optional

from modules.audit.logger import audit_log


class GitLabClient:
    def __init__(self, token: Optional[str] = None, url: Optional[str] = None):
        self.token = token or os.getenv("GITLAB_TOKEN")
        self.url = (url or os.getenv("GITLAB_URL") or "https://gitlab.com").rstrip("/")
        self._api_base = f"{self.url}/api/v4"

    def _headers(self):
        return {
            "PRIVATE-TOKEN": self.token,
            "User-Agent": "JARVIS-Enterprise",
        }

    def _request(self, method: str, path: str, **kwargs):
        import requests

        url = f"{self._api_base}{path}"
        response = requests.request(
            method,
            url,
            headers=self._headers(),
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def list_projects(self, search: Optional[str] = None) -> list[dict]:
        params = {"per_page": 50, "membership": True}
        if search:
            params["search"] = search

        projects = self._request("GET", "/projects", params=params)
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "path_with_namespace": p["path_with_namespace"],
                "description": p.get("description"),
                "url": p.get("web_url"),
                "default_branch": p.get("default_branch"),
                "visibility": p.get("visibility"),
                "last_activity": p.get("last_activity_at"),
            }
            for p in projects
        ]

    def get_project(self, project_id: int) -> dict:
        project = self._request("GET", f"/projects/{project_id}")
        return {
            "id": project["id"],
            "name": project["name"],
            "path_with_namespace": project["path_with_namespace"],
            "description": project.get("description"),
            "url": project.get("web_url"),
            "default_branch": project.get("default_branch"),
            "visibility": project.get("visibility"),
            "created_at": project.get("created_at"),
            "last_activity": project.get("last_activity_at"),
        }

    def list_commits(self, project_id: int, branch: str = "main", since: Optional[str] = None) -> list[dict]:
        params = {"ref_name": branch, "per_page": 30}
        if since:
            params["since"] = since

        commits = self._request("GET", f"/projects/{project_id}/repository/commits", params=params)
        return [
            {
                "sha": c["short_id"],
                "message": c["title"],
                "author": c.get("author_name", "unknown"),
                "date": c.get("committed_date", c.get("created_at")),
                "url": c.get("web_url"),
            }
            for c in commits
        ]

    def list_merge_requests(self, project_id: int, state: str = "opened") -> list[dict]:
        mrs = self._request(
            "GET",
            f"/projects/{project_id}/merge_requests",
            params={"state": state, "per_page": 30},
        )
        return [
            {
                "iid": mr["iid"],
                "title": mr["title"],
                "state": mr["state"],
                "author": mr["author"]["name"],
                "created_at": mr["created_at"],
                "url": mr.get("web_url"),
                "description": (mr.get("description") or "")[:500],
            }
            for mr in mrs
        ]

    def list_pipelines(self, project_id: int, status: Optional[str] = None) -> list[dict]:
        params = {"per_page": 20}
        if status:
            params["status"] = status

        pipelines = self._request("GET", f"/projects/{project_id}/pipelines", params=params)
        return [
            {
                "id": p["id"],
                "status": p["status"],
                "ref": p["ref"],
                "sha": p["sha"][:8],
                "created_at": p.get("created_at"),
                "url": p.get("web_url"),
            }
            for p in pipelines
        ]

    def get_file_content(self, project_id: int, path: str, branch: str = "main") -> Optional[str]:
        try:
            from urllib.parse import quote

            encoded_path = quote(path, safe="")
            data = self._request(
                "GET",
                f"/projects/{project_id}/repository/files/{encoded_path}",
                params={"ref": branch},
            )
            if data.get("content"):
                import base64

                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return None
        except Exception:
            return None

    def get_project_tree(self, project_id: int, branch: str = "main") -> list[dict]:
        try:
            data = self._request(
                "GET",
                f"/projects/{project_id}/repository/tree",
                params={"ref": branch, "per_page": 100, "recursive": True},
            )
            return [
                {"path": item["path"], "type": item["type"], "size": item.get("size", 0)}
                for item in data
            ]
        except Exception:
            return []

    def get_mr_diff_summary(self, project_id: int, mr_iid: int) -> str:
        import requests

        mr = self._request("GET", f"/projects/{project_id}/merge_requests/{mr_iid}")
        changes = self._request("GET", f"/projects/{project_id}/merge_requests/{mr_iid}/changes")

        summary_lines = [
            f"## MR !{mr_iid}: {mr.get('title', '')}",
            f"**Autor:** {mr.get('author', {}).get('name', 'unknown')}",
            f"**Descrição:** {(mr.get('description') or '')[:300]}",
        ]

        diff_files = changes.get("changes", [])
        summary_lines.append(f"\n### Arquivos modificados ({len(diff_files)}):")
        for f in diff_files[:20]:
            summary_lines.append(f"- {f.get('old_path', f.get('new_path', ''))} ({f.get('diff', '')[:50]}...)")

        return "\n".join(summary_lines)

    def check_health(self) -> bool:
        try:
            self._request("GET", "/version")
            return True
        except Exception:
            return False
