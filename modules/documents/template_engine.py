import json
import os
import re
from pathlib import Path
from typing import Optional

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

AREA_POR_ROLE = {
    "admin": None,
    "tech": "tech",
    "security": "tech",
    "marketing": "marketing",
    "finance": "finance",
    "legal": "legal",
    "rh": "rh",
    "user": None,
}


def _pasta_role(username: str) -> str | None:
    from modules.permissions.rbac import get_user_roles

    roles = get_user_roles(username)
    for r in roles:
        area = AREA_POR_ROLE.get(r["name"])
        if area:
            return area
    return None


def listar_templates(username: str) -> list[dict]:
    pasta = _pasta_role(username)
    templates = []
    roles_dirs = [pasta] if pasta else [d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir()]

    for role_dir in roles_dirs:
        dir_path = TEMPLATES_DIR / role_dir
        if not dir_path.exists():
            continue
        for f in sorted(dir_path.glob("*.json")):
            try:
                with open(f, encoding="utf-8") as fh:
                    tmpl = json.load(fh)
                    templates.append({
                        "id": tmpl["id"],
                        "name": tmpl["name"],
                        "role": tmpl["role"],
                        "description": tmpl["description"],
                        "placeholders": tmpl.get("placeholders", []),
                    })
            except Exception:
                pass
    return templates


def carregar_template(template_id: str) -> Optional[dict]:
    for dir_path in TEMPLATES_DIR.iterdir():
        if not dir_path.is_dir():
            continue
        for f in dir_path.glob("*.json"):
            try:
                with open(f, encoding="utf-8") as fh:
                    tmpl = json.load(fh)
                    if tmpl["id"] == template_id:
                        return tmpl
            except Exception:
                pass
    return None


def preencher_template(template: dict, valores: dict) -> list[dict]:
    def _substituir(texto: str) -> str:
        def _replacer(m):
            chave = m.group(1)
            return str(valores.get(chave, m.group(0)))
        return re.sub(r"\{\{(\w+)\}\}", _replacer, texto)

    content = []
    for block in template.get("content", []):
        novo = dict(block)
        if "text" in novo:
            novo["text"] = _substituir(novo["text"])
        if novo.get("type") == "table":
            novo["data"] = [[_substituir(str(c)) for c in row] for row in novo.get("data", [])]
        content.append(novo)
    return content


def gerar_documento_de_template(
    template_id: str,
    valores: dict,
    username: str,
    formato: str = "docx",
    filename: Optional[str] = None,
) -> str:
    tmpl = carregar_template(template_id)
    if not tmpl:
        raise ValueError(f"Template '{template_id}' nao encontrado")

    content = preencher_template(tmpl, valores)
    titulo = valores.get("titulo") or tmpl["name"]

    if formato == "docx":
        from modules.documents.docx_generator import generate_docx
        return generate_docx(titulo, content, filename=filename, author=username)
    elif formato == "pdf":
        from modules.documents.pdf_generator import generate_pdf
        return generate_pdf(titulo, content, filename=filename, author=username)
    elif formato == "pptx":
        from modules.documents.pptx_generator import generate_pptx
        return generate_pptx(titulo, content, filename=filename, author=username)
    else:
        raise ValueError(f"Formato nao suportado: {formato}")
