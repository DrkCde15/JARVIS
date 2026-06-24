import os
import uuid
from pathlib import Path
from typing import Optional

from database.sqlite.connection import get_connection, release_connection

CHROMA_PERSIST_DIR = Path(__file__).resolve().parent.parent.parent / "chroma_db"


class RAGEngine:
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or str(CHROMA_PERSIST_DIR)
        self._chroma_client = None
        self._collection = None
        self._embedding_function = None

    def _lazy_init(self):
        if self._chroma_client is not None:
            return
        try:
            import chromadb
            from chromadb.config import Settings

            self._chroma_client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
            self._embedding_function = self._get_embedding_function()
            self._collection = self._chroma_client.get_or_create_collection(
                name="jarvis_documents",
                embedding_function=self._embedding_function,
            )
        except ImportError:
            raise ImportError(
                "chromadb não instalado. Execute: pip install chromadb"
            )

    def _get_embedding_function(self):
        try:
            from chromadb.utils import embedding_functions

            return embedding_functions.DefaultEmbeddingFunction()
        except Exception:
            try:
                from chromadb.api.embeddings import EmbeddingFunction

                class SimpleEmbeddingFunction(EmbeddingFunction):
                    def __call__(self, texts):
                        import hashlib

                        result = []
                        for text in texts:
                            h = hashlib.md5(text.encode())
                            vec = [ord(c) / 255.0 for c in h.hexdigest()[:16]]
                            while len(vec) < 384:
                                vec.extend(vec[: min(16, 384 - len(vec))])
                            result.append(vec[:384])
                        return result

                return SimpleEmbeddingFunction()
            except Exception:
                return None

    def index_document(self, doc_id: str, chunks: list[str], metadata: Optional[dict] = None):
        self._lazy_init()
        if not chunks:
            return

        metadata = metadata or {}
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {**metadata, "doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))
        ]

        self._collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas,
        )

    def search(self, query: str, n_results: int = 5, filter_doc_id: Optional[str] = None, department: Optional[str] = None):
        self._lazy_init()
        where = {}
        if filter_doc_id:
            where["doc_id"] = filter_doc_id
        if department:
            where["department"] = department
        where = where if where else None

        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )

        documents = results.get("documents", [[]])[0] if results.get("documents") else []
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
        distances = results.get("distances", [[]])[0] if results.get("distances") else []

        return [
            {
                "content": documents[i],
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "score": 1.0 - distances[i] if i < len(distances) else 0.0,
            }
            for i in range(len(documents))
        ]

    def delete_document(self, doc_id: str):
        self._lazy_init()
        self._collection.delete(where={"doc_id": doc_id})

    def list_documents(self) -> list[str]:
        self._lazy_init()
        all_metadata = self._collection.get()["metadatas"]
        doc_ids = set()
        for m in all_metadata:
            if m and "doc_id" in m:
                doc_ids.add(m["doc_id"])
        return sorted(doc_ids)

    def get_collection_stats(self) -> dict:
        self._lazy_init()
        count = self._collection.count()
        return {"total_chunks": count, "collection_name": "jarvis_documents"}
