import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel

from api.middleware import get_current_user, require_permission
from modules.rag.processor import DocumentProcessor
from modules.rag.search import SemanticSearch
from modules.audit.logger import audit_log

router = APIRouter()
processor = DocumentProcessor()
searcher = SemanticSearch()

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    username: str = Depends(require_permission("documents", "upload")),
):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename).suffix.lower()
    supported = {".pdf", ".docx", ".pptx", ".txt", ".md"}
    if file_ext not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado: {file_ext}. Use: {', '.join(supported)}",
        )

    file_id = str(uuid.uuid4())
    safe_name = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / safe_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        doc_id = processor.process_and_store(
            file_path=str(file_path),
            username=username,
            filename=safe_name,
            original_name=file.filename,
            file_type=file_ext,
            file_size=len(content),
        )

        audit_log(
            username=username,
            action="document_upload",
            resource="rag",
            resource_id=doc_id,
            details=f"Arquivo: {file.filename} ({len(content)} bytes)",
            status="success",
        )

        return {
            "message": "Documento processado e indexado",
            "document_id": doc_id,
            "filename": file.filename,
            "file_size": len(content),
        }
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")


@router.post("/search")
async def search_documents(
    req: SearchRequest,
    username: str = Depends(require_permission("rag", "search")),
):
    results = searcher.search(req.query, n_results=req.n_results, username=username)
    audit_log(
        username=username,
        action="semantic_search",
        resource="rag",
        details=f"Query: {req.query[:100]}",
        status="success",
    )
    return {"query": req.query, "results": results, "count": len(results)}


@router.post("/search/context")
async def search_with_context(
    req: SearchRequest,
    username: str = Depends(require_permission("rag", "search")),
):
    context = searcher.search_with_context(req.query, n_results=req.n_results, username=username)
    return {"query": req.query, "context": context}


@router.get("/documents")
async def list_documents(
    username: str = Depends(get_current_user),
):
    from modules.rag.search import _departamento_do_usuario
    department = _departamento_do_usuario(username)
    return processor.list_documents(username=username, department=department)


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    username: str = Depends(get_current_user),
):
    doc = processor.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return doc


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    username: str = Depends(require_permission("documents", "delete")),
):
    processor.delete_document(doc_id)
    audit_log(username, "document_delete", resource="rag", resource_id=doc_id, status="success")
    return {"message": "Documento deletado"}


@router.get("/stats")
async def rag_stats(
    username: str = Depends(require_permission("rag", "search")),
):
    try:
        from modules.rag.engine import RAGEngine

        engine = RAGEngine()
        stats = engine.get_collection_stats()
        docs = processor.list_documents()
        stats["total_documents"] = len(docs)
        return stats
    except Exception as e:
        return {"error": str(e), "total_documents": 0, "total_chunks": 0}
