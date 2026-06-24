import os
import base64
from typing import Optional

from modules.audit.logger import audit_log


class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self._api_base = "https://api.github.com"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
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

    def list_repos(self, username: Optional[str] = None) -> list[dict]:
        endpoint = f"/users/{username}/repos" if username else "/user/repos"
        repos = self._request("GET", endpoint)
        return [
            {
                "name": r["name"],
                "full_name": r["full_name"],
                "description": r.get("description"),
                "url": r["html_url"],
                "language": r.get("language"),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "private": r.get("private", False),
            }
            for r in repos
        ]

    def get_repo(self, repo_full: str) -> dict:
        repo = self._request("GET", f"/repos/{repo_full}")
        return {
            "name": repo["name"],
            "full_name": repo["full_name"],
            "description": repo.get("description"),
            "url": repo["html_url"],
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "private": repo.get("private", False),
            "default_branch": repo.get("default_branch"),
            "created_at": repo.get("created_at"),
            "updated_at": repo.get("updated_at"),
        }

    def list_commits(self, repo_full: str, branch: str = "main", since: Optional[str] = None) -> list[dict]:
        params = {"sha": branch, "per_page": 30}
        if since:
            params["since"] = since

        import requests

        url = f"{self._api_base}/repos/{repo_full}/commits"
        response = requests.get(url, headers=self._headers(), params=params, timeout=30)
        response.raise_for_status()
        commits = response.json()

        return [
            {
                "sha": c["sha"][:8],
                "message": c["commit"]["message"].split("\n")[0],
                "author": c["commit"]["author"]["name"],
                "date": c["commit"]["author"]["date"],
                "url": c["html_url"],
            }
            for c in commits
        ]

    def list_pull_requests(self, repo_full: str, state: str = "open") -> list[dict]:
        prs = self._request("GET", f"/repos/{repo_full}/pulls", params={"state": state, "per_page": 30})
        return [
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "author": pr["user"]["login"],
                "created_at": pr["created_at"],
                "url": pr["html_url"],
                "body": pr.get("body", "")[:500],
            }
            for pr in prs
        ]

    def get_file_content(self, repo_full: str, path: str, branch: str = "main") -> Optional[str]:
        try:
            data = self._request("GET", f"/repos/{repo_full}/contents/{path}", params={"ref": branch})
            if isinstance(data, dict) and data.get("content"):
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return None
        except Exception:
            return None

    def get_repo_tree(self, repo_full: str, branch: str = "main") -> list[dict]:
        try:
            data = self._request("GET", f"/repos/{repo_full}/git/trees/{branch}", params={"recursive": "1"})
            return [
                {"path": item["path"], "type": item["type"], "size": item.get("size", 0)}
                for item in data.get("tree", [])
            ]
        except Exception:
            return []

    def get_diff_summary(self, repo_full: str, pr_number: int) -> str:
        import requests

        url = f"{self._api_base}/repos/{repo_full}/pulls/{pr_number}"
        pr = requests.get(url, headers=self._headers(), timeout=30).json()

        files_url = pr.get("url", "") + "/files"
        files_resp = requests.get(files_url, headers=self._headers(), timeout=30)
        files = files_resp.json() if files_resp.ok else []

        summary_lines = [
            f"## PR #{pr_number}: {pr.get('title', '')}",
            f"**Autor:** {pr.get('user', {}).get('login', 'unknown')}",
            f"**Descrição:** {(pr.get('body') or '')[:300]}",
            f"\n### Arquivos modificados ({len(files)}):",
        ]
        for f in files[:20]:
            summary_lines.append(f"- {f.get('filename', '')} ({f.get('status', '')}, +{f.get('additions', 0)}/-{f.get('deletions', 0)})")

        return "\n".join(summary_lines)

    def check_health(self) -> bool:
        try:
            self._request("GET", "/rate_limit")
            return True
        except Exception:
            return False
