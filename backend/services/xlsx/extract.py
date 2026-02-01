from __future__ import annotations

import openpyxl

from backend.contracts import make_block
from backend.services.extract_utils import (
    is_exact_term_match,
    is_garbage_text,
    is_numeric_only,
    is_technical_terms_only,
)


def extract_blocks(xlsx_path: str) -> dict:
    """
    Extract text blocks from an Excel file.

    Returns standard block format compatible with the translation pipeline.
    Uses read_only mode for performance with large files.
    """
    # Use read_only=False if we need dimensions/hidden status reliably,
    # but read_only=True is much faster for large files.
    # To get hidden status, we must use read_only=False or accept it
    # might be missing.
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    blocks: list[dict] = []

    # Track metadata for the whole document
    for sheet_index, sheet_name in enumerate(wb.sheetnames):
        ws = wb[sheet_name]
        is_sheet_hidden = ws.sheet_state != "visible"

        # Unique ID counter for blocks in this sheet
        block_id_counter = 0

        # Iterate through all cells that have values
        for row_idx, row in enumerate(ws.iter_rows(), start=1):
            # Check if row is hidden
            is_row_hidden = (
                ws.row_dimensions[row_idx].hidden if row_idx in ws.row_dimensions else False
            )

            for cell in row:
                if cell.value is None:
                    continue

                # Check if column is hidden
                col_letter = cell.column_letter
                is_col_hidden = (
                    ws.column_dimensions[col_letter].hidden
                    if col_letter in ws.column_dimensions
                    else False
                )

                # Skip common Excel error values (#REF!, #DIV/0!, etc.)
                cell_val_str = str(cell.value).strip()
                if cell_val_str.startswith("#") and any(
                    err in cell_val_str for err in ["REF!", "DIV/0!", "VALUE!", "N/A", "NAME?"]
                ):
                    continue

                # Detect if cell contains a formula
                # Note: with data_only=True, cell.value is the RESULT.
                # To see the formula, we'd need another pass or different load_workbook params.
                # However, the requirement is to PROTECT formulas during APPLY.
                # In EXTRACT with data_only=True, we get what the user sees.

                # Convert to string and clean
                text = cell_val_str

                # Use heuristics to filter non-translatable content
                if (
                    not text
                    or is_numeric_only(text)
                    or is_exact_term_match(text)
                    or is_technical_terms_only(text)
                    or is_garbage_text(text)
                ):
                    continue

                block_id_counter += 1
                shape_id = block_id_counter

                # Standard block with extra Excel-specific fields
                block = make_block(
                    slide_index=sheet_index,
                    shape_id=shape_id,
                    block_type="spreadsheet_cell",
                    source_text=text,
                )

                # Assign a unique client_id for correction mode tracking
                block["client_id"] = f"xlsx-{sheet_index}-{shape_id}"

                # Add Excel-specific metadata for reconstruction
                block["sheet_name"] = sheet_name
                block["cell_address"] = cell.coordinate
                block["is_hidden"] = is_sheet_hidden or is_row_hidden or is_col_hidden

                # Check for formula in a separate pass if needed, but for now mark as potential translatable
                # We will handle formula protection in apply.py by loading with data_only=False.

                blocks.append(block)

    return {
        "blocks": blocks,
        "sheet_count": len(wb.sheetnames),
    }
