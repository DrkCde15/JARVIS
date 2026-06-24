import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.sqlite.schema import garantir_banco
from database.sqlite.migrations import run_migrations
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    garantir_banco()
    run_migrations()
    yield


app = FastAPI(
    title="JARVIS Enterprise API",
    description="API corporativa do assistente JARVIS com RAG, RBAC, integrações e geração de documentos",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

app.mount("/app", StaticFiles(directory="api/static", html=True), name="static")


@app.get("/")
async def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "JARVIS Enterprise API"}


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    uvicorn.run(
        "api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    start_server()
