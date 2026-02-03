from __future__ import annotations

import io
from xml.sax.saxutils import escape


def export_to_pdf(
    blocks: list[dict],
    filename: str = "translation",
) -> io.BytesIO:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as e:
        raise ImportError(
            "PDF 匯出需要 reportlab。請安裝: pip install reportlab"
        ) from e

    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))

    styles = getSampleStyleSheet()
    base_style = ParagraphStyle(
        "CJKBody",
        parent=styles["Normal"],
        fontName="MSung-Light",
        fontSize=10,
        leading=14,
    )
    title_style = ParagraphStyle(
        "CJKTitle",
        parent=styles["Title"],
        fontName="MSung-Light",
        fontSize=16,
        leading=20,
    )

    elements = [Paragraph("翻譯對照表", title_style), Spacer(1, 12)]

    data = [["#", "原文", "譯文"]]
    for idx, block in enumerate(blocks, 1):
        original = escape(block.get("original_text") or block.get("source_text") or block.get("text") or "")
        translated = escape(block.get("translated_text") or block.get("target_text") or "")
        original = original.replace("\n", "<br/>")
        translated = translated.replace("\n", "<br/>")
        data.append(
            [
                str(idx),
                Paragraph(original, base_style),
                Paragraph(translated, base_style),
            ]
        )

    index_width = 32
    text_width = (doc.width - index_width) / 2
    table = Table(data, colWidths=[index_width, text_width, text_width])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "MSung-Light"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F8FAFC")],
                ),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)
    output.seek(0)
    return output
