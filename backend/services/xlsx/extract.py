from __future__ import annotations

from pathlib import Path
from typing import Iterable

import openpyxl
from backend.contracts import make_block
from backend.services.extract_utils import is_numeric_only, is_technical_terms_only


def extract_blocks(xlsx_path: str) -> dict:
    """
    Extract text blocks from an Excel file.
    
    Returns standard block format compatible with the translation pipeline.
    """
    wb = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)
    blocks: list[dict] = []
    
    # We use sheet_index as slide_index for compatibility
    for sheet_index, sheet_name in enumerate(wb.sheetnames):
        ws = wb[sheet_name]
        
        # Unique ID counter for blocks in this sheet
        block_id_counter = 0
        
        # Iterate through all cells that have values
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                
                # Convert to string and clean
                text = str(cell.value).strip()
                
                if not text or is_numeric_only(text) or is_technical_terms_only(text):
                    continue
                
                # Create a unique shape_id (int) for this cell
                # We can use row*1000 + col for simplicity if we assume < 1000 columns
                # Or just a simple counter
                block_id_counter += 1
                shape_id = block_id_counter
                
                # Standard block with extra Excel-specific fields
                block = make_block(
                    slide_index=sheet_index,
                    shape_id=shape_id,
                    block_type="table_cell", # Reuse table_cell type
                    source_text=text
                )
                
                # Add Excel-specific metadata
                block["sheet_name"] = sheet_name
                block["cell_address"] = cell.coordinate
                
                blocks.append(block)
                
    return {
        "blocks": blocks,
        "sheet_count": len(wb.sheetnames)
    }
