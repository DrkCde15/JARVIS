import os
import tempfile
import pytest
from pathlib import Path


class TestDocxGeneration:
    def test_generate_docx(self):
        from modules.documents.docx_generator import generate_docx

        content = [
            {"type": "heading1", "text": "Introduction"},
            {"type": "paragraph", "text": "This is a test document."},
            {"type": "heading2", "text": "Details"},
            {"type": "paragraph", "text": "More content here."},
        ]

        output_path = generate_docx(
            title="Test Document",
            content=content,
            filename="test_doc.docx",
            author="Test",
        )

        assert os.path.exists(output_path)
        assert output_path.endswith(".docx")
        os.remove(output_path)


class TestPdfGeneration:
    def test_generate_pdf(self):
        from modules.documents.pdf_generator import generate_pdf

        content = [
            {"type": "heading1", "text": "Report Title"},
            {"type": "paragraph", "text": "This is a test PDF report."},
            {"type": "table", "data": [["Name", "Value"], ["Item 1", "100"], ["Item 2", "200"]]},
        ]

        output_path = generate_pdf(
            title="Test PDF",
            content=content,
            filename="test_report.pdf",
            author="Test",
        )

        assert os.path.exists(output_path)
        assert output_path.endswith(".pdf")
        os.remove(output_path)


class TestPptxGeneration:
    def test_generate_pptx(self):
        from modules.documents.pptx_generator import generate_pptx

        slides = [
            {"type": "content", "title": "Slide 1", "items": ["Item A", "Item B", "Item C"]},
            {"type": "content", "title": "Slide 2", "content": "Detailed explanation here."},
        ]

        output_path = generate_pptx(
            title="Test Presentation",
            slides=slides,
            filename="test_preso.pptx",
            author="Test",
        )

        assert os.path.exists(output_path)
        assert output_path.endswith(".pptx")
        os.remove(output_path)
