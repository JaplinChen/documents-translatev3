from copy import copy

import openpyxl

def apply_translations(input_path: str, output_path: str, blocks: list[dict]):
    """Apply translations to the Excel file."""
    # Load with data_only=False to keep formulas
    wb = openpyxl.load_workbook(input_path, data_only=False)

    # Map (sheet_name, cell_address) -> translated_text.
    translations = {}
    for block in blocks:
        sheet_name = block.get("sheet_name")
        cell_address = block.get("cell_address")
        translated_text = block.get("translated_text", "")
        if sheet_name and cell_address:
            translations[(sheet_name, cell_address)] = translated_text

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        for (s_name, addr), text in translations.items():
            if s_name == sheet_name:
                try:
                    # Skills optimization:
                    # Directly updating cell.value keeps cell styles.
                    # openpyxl handles this for non-read-only workbooks.
                    ws[addr] = text
                except Exception:
                    continue

    wb.save(output_path)


def apply_bilingual(
    input_path: str,
    output_path: str,
    blocks: list[dict],
    layout: str = "inline",
):
    """
    Apply bilingual translations back to the Excel file.
    Preserves original styles and optimizes alignment for multi-line content.
    """
    wb = openpyxl.load_workbook(input_path, data_only=False)

    translations = {}
    for block in blocks:
        sheet_name = block.get("sheet_name")
        cell_address = block.get("cell_address")
        source_text = block.get("source_text", "")
        translated_text = block.get("translated_text", "")
        if sheet_name and cell_address:
            # Simple bilingual: Source \n Translated
            translations[(sheet_name, cell_address)] = (
                f"{source_text}\n{translated_text}"
            )

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        for (s_name, addr), text in translations.items():
            if s_name == sheet_name:
                try:
                    cell = ws[addr]
                    cell.value = text

                    # Skills improvement:
                    # Use copy() to avoid mutating shared styles.
                    # sharing the same style object.
                    if cell.alignment:
                        new_alignment = copy(cell.alignment)
                        new_alignment.wrapText = True
                        cell.alignment = new_alignment
                    else:
                        cell.alignment = openpyxl.styles.Alignment(
                            wrapText=True
                        )
                except Exception:
                    continue

    wb.save(output_path)
