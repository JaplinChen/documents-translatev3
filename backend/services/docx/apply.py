from __future__ import annotations

from io import BytesIO

from docx import Document
from docx.shared import RGBColor


def _copy_run_format(source_run, target_run):
    """Deep copy formatting from one run to another."""
    target_run.bold = source_run.bold
    target_run.italic = source_run.italic
    target_run.underline = source_run.underline
    target_run.font.name = source_run.font.name
    target_run.font.size = source_run.font.size
    if source_run.font.color and source_run.font.color.rgb:
        target_run.font.color.rgb = source_run.font.color.rgb


def _set_paragraph_text(paragraph, text, mode="replace", source_text=None):
    """
    Set text for a paragraph.
    mode="replace": Replace entire paragraph content.
    mode="bilingual": Append translated text after original runs.
    """
    if mode == "replace":
        # Clear existing runs
        p_element = paragraph._element
        for run in paragraph.runs:
            p_element.remove(run._element)
        paragraph.add_run(text)
    elif mode == "bilingual" and source_text:
        # Paragraph already contains source_text
        paragraph.add_run("\n")
        new_run = paragraph.add_run(text)
        try:
            new_run.font.color.rgb = RGBColor(0x1F, 0x77, 0xB4)  # Accent color
        except Exception:
            pass


def apply_translations(  # noqa: C901
    docx_in: str | bytes,
    docx_out: str,
    blocks: list[dict],
    mode: str = "direct",
    target_language: str | None = None,
) -> None:
    """Apply translations to a .docx file."""
    if isinstance(docx_in, bytes):
        doc = Document(BytesIO(docx_in))
    else:
        doc = Document(docx_in)

    # Simple mapping: block_idx -> text
    # For Word, we use slide_index as paragraph/table index
    para_map = {b["slide_index"]: b for b in blocks if b.get("block_type") == "textbox"}
    table_map = {}  # complex key: t{table_idx}_r{row_idx}_c{cell_idx}
    for b in blocks:
        if b.get("block_type") == "table_cell":
            table_map[b.get("shape_id")] = b

    # 1. Apply to Paragraphs
    for i, para in enumerate(doc.paragraphs):
        if i in para_map:
            block = para_map[i]
            translated = block.get("translated_text", "")
            if not translated:
                continue

            if mode == "bilingual":
                _set_paragraph_text(
                    para,
                    translated,
                    mode="bilingual",
                    source_text=block.get("source_text"),
                )
            else:
                _set_paragraph_text(para, translated, mode="replace")

    # 2. Apply to Tables
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                shape_id = t_idx * 1000 + r_idx * 100 + c_idx
                if shape_id in table_map:
                    block = table_map[shape_id]
                    translated = block.get("translated_text", "")
                    if not translated:
                        continue

                    if mode == "bilingual":
                        # For cells, we might want to just append or replace
                        source_text = block.get("source_text", "")
                        cell.text = f"{source_text}\n{translated}"
                    else:
                        cell.text = translated

    doc.save(docx_out)


def apply_bilingual(docx_in, docx_out, blocks, **kwargs):
    apply_translations(docx_in, docx_out, blocks, mode="bilingual")


def apply_chinese_corrections(docx_in, docx_out, blocks, **kwargs):
    # For now, correction in Word just replaces the text
    apply_translations(docx_in, docx_out, blocks, mode="direct")
