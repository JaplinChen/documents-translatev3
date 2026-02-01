from copy import copy

import openpyxl
from openpyxl.styles import Alignment, Font

# Standard colors from xlsx.md
COLOR_BLUE = "0000FF"


def apply_translations(input_path: str, output_path: str, blocks: list[dict]):
    """
    Apply translations to the Excel file.
    Follows xlsx.md: Blue text for hardcoded inputs/translations.
    """
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
                    cell = ws[addr]

                    # PROTECT FORMULAS: Do not overwrite if it's a formula
                    # In data_only=False mode, if cell.value starts with '=', it's a formula.
                    if isinstance(cell.value, str) and cell.value.startswith("="):
                        continue

                    cell.value = text

                    # Apply Blue color for hardcoded translations (per xlsx.md)
                    if cell.font:
                        new_font = copy(cell.font)
                        new_font.color = COLOR_BLUE
                        cell.font = new_font
                    else:
                        cell.font = Font(color=COLOR_BLUE)

                except Exception:
                    continue

    wb.save(output_path)

    # NEW: Trigger formula recalculation and error scanning
    from backend.services.xlsx.recalc import recalc_xlsx

    try:
        recalc_result = recalc_xlsx(output_path)
        # We could log this or return it to the caller if needed
        # For now, it ensures the file is updated by LibreOffice engine
    except Exception:
        pass


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
            translations[(sheet_name, cell_address)] = f"{source_text}\n{translated_text}"

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        for (s_name, addr), text in translations.items():
            if s_name == sheet_name:
                try:
                    cell = ws[addr]

                    # PROTECT FORMULAS
                    if isinstance(cell.value, str) and cell.value.startswith("="):
                        continue

                    cell.value = text

                    # Apply Blue color to the whole cell for bilingual
                    if cell.font:
                        new_font = copy(cell.font)
                        new_font.color = COLOR_BLUE
                        cell.font = new_font
                    else:
                        cell.font = Font(color=COLOR_BLUE)

                    # Ensure wrapText is True for multi-line bilingual content
                    if cell.alignment:
                        new_alignment = copy(cell.alignment)
                        new_alignment.wrapText = True
                        cell.alignment = new_alignment
                    else:
                        cell.alignment = Alignment(wrapText=True)
                except Exception:
                    continue

    wb.save(output_path)

    # NEW: Trigger formula recalculation and error scanning
    from backend.services.xlsx.recalc import recalc_xlsx

    try:
        recalc_xlsx(output_path)
    except Exception:
        pass
