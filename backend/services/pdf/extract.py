from __future__ import annotations

import fitz  # PyMuPDF
from backend.contracts import make_block
from backend.services.extract_utils import is_numeric_only, is_technical_terms_only


def extract_blocks(pdf_path: str) -> dict:
    """
    Extract text blocks from a PDF file using PyMuPDF.
    
    Returns blocks with coordinate information for potential overlay or reconstruction.
    """
    doc = fitz.open(pdf_path)
    blocks: list[dict] = []
    
    for page_index, page in enumerate(doc):
        # Unique ID counter for blocks in this page
        block_id_counter = 0
        
        # Get text blocks with coordinates
        # block contains: (x0, y0, x1, y1, "text", block_no, block_type)
        page_blocks = page.get_text("blocks")
        
        for b in page_blocks:
            x0, y0, x1, y1, text, block_no, block_type = b
            
            # block_type 0 is text
            if block_type != 0:
                continue
                
            text = text.strip()
            if not text or is_numeric_only(text) or is_technical_terms_only(text):
                continue
            
            block_id_counter += 1
            shape_id = block_id_counter
            
            # PDF coordinates are in points (1/72 inch)
            width = x1 - x0
            height = y1 - y0
            
            block = make_block(
                slide_index=page_index,
                shape_id=shape_id,
                block_type="textbox", # Reuse textbox type
                source_text=text,
                x=x0,
                y=y0,
                width=width,
                height=height
            )
            
            blocks.append(block)
            
    return {
        "blocks": blocks,
        "page_count": len(doc)
    }
