from __future__ import annotations

import openpyxl


def apply_translations(input_path: str, output_path: str, blocks: list[dict]):
    """
    Apply translations back to the Excel file.
    Only handles direct replacement for now.
    """
    wb = openpyxl.load_workbook(input_path)
    
    # Create a mapping for quick lookup: (sheet_name, cell_address) -> translated_text
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
                    ws[addr] = text
                except Exception:
                    continue
                    
    wb.save(output_path)


def apply_bilingual(input_path: str, output_path: str, blocks: list[dict], layout: str = "inline"):
    """
    Apply bilingual translations back to the Excel file.
    In Excel, bilingual usually means "Source \n Target" in the same cell.
    """
    wb = openpyxl.load_workbook(input_path)
    
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
                    ws[addr] = text
                    # Enable wrap text if we added a newline
                    ws[addr].alignment = openpyxl.styles.Alignment(wrapText=True)
                except Exception:
                    continue
                    
    wb.save(output_path)
