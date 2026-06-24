import os
from pathlib import Path
from typing import Optional

from modules.documents.base import ensure_output_dir, safe_filename


def generate_pdf(
    title: str,
    content: list[dict],
    filename: Optional[str] = None,
    author: str = "JARVIS",
) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        ListFlowable,
        ListItem,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    output_dir = ensure_output_dir("pdf")
    name = filename or safe_filename(title)
    if not name.endswith(".pdf"):
        name += ".pdf"

    output_path = output_dir / name
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=20,
        textColor=HexColor("#1a1a2e"),
    )
    heading1_style = ParagraphStyle(
        "CustomH1",
        parent=styles["Heading1"],
        fontSize=16,
        spaceBefore=16,
        spaceAfter=8,
        textColor=HexColor("#16213e"),
    )
    heading2_style = ParagraphStyle(
        "CustomH2",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=6,
        textColor=HexColor("#0f3460"),
    )
    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )
    code_style = ParagraphStyle(
        "Code",
        parent=styles["Code"],
        fontSize=8,
        leading=10,
        leftIndent=10,
        spaceAfter=6,
        backColor=HexColor("#f5f5f5"),
    )

    elements = []
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.5 * cm))

    for block in content:
        block_type = block.get("type", "paragraph")
        text = block.get("text", "")

        if block_type == "heading1":
            elements.append(Paragraph(text, heading1_style))
        elif block_type == "heading2":
            elements.append(Paragraph(text, heading2_style))
        elif block_type == "paragraph":
            elements.append(Paragraph(text, normal_style))
        elif block_type == "code":
            elements.append(Paragraph(f"<pre>{text}</pre>", code_style))
        elif block_type == "table":
            table_data = block.get("data", [])
            if table_data:
                cols = max(len(r) for r in table_data)
                t = Table(table_data, colWidths=[doc.width / cols] * cols)
                t.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#16213e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f5f5f5")]),
                    ])
                )
                elements.append(t)
                elements.append(Spacer(1, 0.3 * cm))
        elif block_type == "page_break":
            elements.append(PageBreak())

    doc.build(elements)
    return str(output_path)
