import os
import tempfile
import pytest
from pathlib import Path


class TestDocumentProcessor:
    def test_extract_txt(self):
        from modules.rag.processor import DocumentProcessor

        processor = DocumentProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Hello, this is a test document.")
            tmp_path = f.name

        try:
            text = processor.extract_text(tmp_path)
            assert "Hello" in text
            assert "test document" in text
        finally:
            os.unlink(tmp_path)

    def test_extract_md(self):
        from modules.rag.processor import DocumentProcessor

        processor = DocumentProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Title\n\nThis is a **markdown** file.")
            tmp_path = f.name

        try:
            text = processor.extract_text(tmp_path)
            assert "Title" in text
            assert "markdown" in text
        finally:
            os.unlink(tmp_path)

    def test_chunk_text_small(self):
        from modules.rag.processor import DocumentProcessor

        processor = DocumentProcessor()
        chunks = processor.chunk_text("Short text.", chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0] == "Short text."

    def test_chunk_text_large(self):
        from modules.rag.processor import DocumentProcessor

        processor = DocumentProcessor()
        text = "word " * 1000
        chunks = processor.chunk_text(text, chunk_size=200, overlap=20)
        assert len(chunks) >= 5

    def test_chunk_text_empty(self):
        from modules.rag.processor import DocumentProcessor

        processor = DocumentProcessor()
        chunks = processor.chunk_text("")
        assert chunks == []

    def test_chunk_text_whitespace(self):
        from modules.rag.processor import DocumentProcessor

        processor = DocumentProcessor()
        chunks = processor.chunk_text("   ")
        assert chunks == []

    def test_unsupported_format(self):
        from modules.rag.processor import DocumentProcessor

        processor = DocumentProcessor()
        with pytest.raises(ValueError, match="Formato não suportado"):
            processor.extract_text("test.exe")


class TestRAGEngine:
    def test_engine_initialization(self):
        from modules.rag.engine import RAGEngine

        engine = RAGEngine(persist_directory=tempfile.mkdtemp())
        assert engine.persist_directory is not None
