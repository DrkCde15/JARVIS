from typing import Optional

from modules.rag.engine import RAGEngine

AREA_POR_ROLE = {
    "admin": "Administração",
    "tech": "Tecnologia",
    "security": "Segurança",
    "marketing": "Marketing",
    "finance": "Financeiro",
    "legal": "Jurídico",
    "rh": "Recursos Humanos",
    "user": "Geral",
}


def _departamento_do_usuario(username: str) -> str | None:
    from modules.permissions.rbac import get_user_roles

    roles = get_user_roles(username)
    for r in roles:
        if r["name"] == "admin":
            return None
        area = AREA_POR_ROLE.get(r["name"])
        if area:
            return area
    return "Geral"


class SemanticSearch:
    def __init__(self):
        self.engine = RAGEngine()

    def search(self, query: str, n_results: int = 5, username: Optional[str] = None):
        department = _departamento_do_usuario(username) if username else None
        try:
            return self.engine.search(query, n_results=n_results, department=department)
        except Exception:
            return self._fallback_search(query, username)

    def _fallback_search(self, query: str, username: Optional[str] = None):
        from database.sqlite.connection import get_connection, release_connection

        conn = get_connection()
        try:
            cursor = conn.cursor()
            conditions = ["1=1"]
            params = []
            department = _departamento_do_usuario(username) if username else None

            if department:
                conditions.append("d.department = ?")
                params.append(department)
            elif username:
                conditions.append("d.username = ?")
                params.append(username)

            where = " AND ".join(conditions)
            rows = cursor.execute(
                f"""
                SELECT dc.content, d.original_name, d.file_type, d.username
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE {where}
                ORDER BY dc.created_at DESC
                LIMIT ?
                """,
                tuple(params + [10]),
            ).fetchall()

            query_lower = query.lower()
            scored = []
            for row in rows:
                content = row["content"]
                score = content.lower().count(query_lower) / max(len(content.split()), 1)
                if score > 0:
                    scored.append({
                        "content": content,
                        "metadata": {
                            "filename": row["original_name"],
                            "file_type": row["file_type"],
                            "username": row["username"],
                        },
                        "score": min(score * 10, 1.0),
                    })

            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:5]

        finally:
            release_connection(conn)

    def search_with_context(self, query: str, n_results: int = 5, username: Optional[str] = None) -> str:
        results = self.search(query, n_results, username)
        if not results:
            return ""

        context_parts = []
        for r in results:
            source = r["metadata"].get("filename", "desconhecido")
            context_parts.append(f"[Fonte: {source}]\n{r['content']}")

        return "\n\n---\n\n".join(context_parts)
