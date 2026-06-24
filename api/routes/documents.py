from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api.middleware import get_current_user, require_permission
from modules.documents import generate_docx, generate_pdf, generate_pptx
from modules.documents.template_engine import listar_templates, gerar_documento_de_template
from modules.audit.logger import audit_log

router = APIRouter()


class ContentBlock(BaseModel):
    type: str = "paragraph"
    text: str = ""
    style: Optional[str] = None
    data: Optional[list[list[str]]] = None


class DocxRequest(BaseModel):
    title: str
    content: list[ContentBlock]
    filename: Optional[str] = None
    author: str = "JARVIS"


class PdfRequest(BaseModel):
    title: str
    content: list[ContentBlock]
    filename: Optional[str] = None
    author: str = "JARVIS"


class SlideBlock(BaseModel):
    type: str = "content"
    title: str = ""
    items: Optional[list[str]] = None
    content: Optional[str] = None


class PptxRequest(BaseModel):
    title: str
    slides: list[SlideBlock]
    filename: Optional[str] = None
    author: str = "JARVIS"


@router.post("/docx")
async def create_docx(
    req: DocxRequest,
    username: str = Depends(require_permission("documents", "generate")),
):
    try:
        content_dicts = [b.model_dump() for b in req.content]
        output_path = generate_docx(
            title=req.title,
            content=content_dicts,
            filename=req.filename,
            author=req.author,
        )
        audit_log(
            username=username,
            action="generate_docx",
            resource="documents",
            details=f"Título: {req.title}",
            status="success",
        )
        return {"message": "Documento gerado", "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar DOCX: {str(e)}")


@router.post("/pdf")
async def create_pdf(
    req: PdfRequest,
    username: str = Depends(require_permission("documents", "generate")),
):
    try:
        content_dicts = [b.model_dump() for b in req.content]
        output_path = generate_pdf(
            title=req.title,
            content=content_dicts,
            filename=req.filename,
            author=req.author,
        )
        audit_log(
            username=username,
            action="generate_pdf",
            resource="documents",
            details=f"Título: {req.title}",
            status="success",
        )
        return {"message": "Documento gerado", "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")


@router.post("/pptx")
async def create_pptx(
    req: PptxRequest,
    username: str = Depends(require_permission("documents", "generate")),
):
    try:
        slides_dicts = [s.model_dump() for s in req.slides]
        output_path = generate_pptx(
            title=req.title,
            slides=slides_dicts,
            filename=req.filename,
            author=req.author,
        )
        audit_log(
            username=username,
            action="generate_pptx",
            resource="documents",
            details=f"Título: {req.title}",
            status="success",
        )
        return {"message": "Documento gerado", "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PPTX: {str(e)}")


class TemplateGenerateRequest(BaseModel):
    template_id: str
    valores: dict
    format: str = "docx"
    filename: Optional[str] = None


@router.get("/templates")
async def list_templates_endpoint(
    username: str = Depends(require_permission("documents", "generate")),
):
    templates = listar_templates(username)
    return {"templates": templates, "count": len(templates)}


@router.post("/templates/generate")
async def generate_from_template(
    req: TemplateGenerateRequest,
    username: str = Depends(require_permission("documents", "generate")),
):
    try:
        output_path = gerar_documento_de_template(
            template_id=req.template_id,
            valores=req.valores,
            username=username,
            formato=req.format,
            filename=req.filename,
        )
        audit_log(
            username=username,
            action="generate_from_template",
            resource="documents",
            details=f"Template: {req.template_id}",
            status="success",
        )
        return {"message": "Documento gerado a partir de template", "path": output_path}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar documento: {str(e)}")
