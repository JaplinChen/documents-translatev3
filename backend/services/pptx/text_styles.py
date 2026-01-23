from __future__ import annotations
from typing import Any
from lxml import etree
from pptx.text.text import TextFrame
from backend.services.font_manager import clone_font_props

def capture_full_frame_styles(text_frame: TextFrame) -> list[dict[str, Any]]:
    styles = []
    for p in text_frame.paragraphs:
        # Deep XML capture for high-fidelity replication (Indentation, tab stops, etc)
        p_pr = None
        try:
            p_xml = p._p
            p_pr_xml = p_xml.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}pPr')
            if p_pr_xml is None:
                p_pr_xml = p_xml.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}pPr')
            if p_pr_xml is not None:
                p_pr = etree.tostring(p_pr_xml)
        except Exception: pass

        styles.append({
            "level": p.level,
            "alignment": p.alignment,
            "space_before": p.space_before,
            "space_after": p.space_after,
            "line_spacing": p.line_spacing,
            "font_obj": p.runs[0].font if p.runs else None,
            "bold": p.runs[0].font.bold if p.runs else None,
            "italic": p.runs[0].font.italic if p.runs else None,
            "underline": p.runs[0].font.underline if p.runs else None,
            "has_text": bool(p.text and p.text.strip()),
            "pPr_xml": p_pr
        })
    
    # --- Post-process: Consolidate spacing from empty paragraphs ---
    # Convert empty lines into space_after of previous paragraph or space_before of next
    try:
        last_text_idx = -1
        pending_before = 0
        
        for i, style in enumerate(styles):
            if style["has_text"]:
                # Apply any pending space from initial empty lines to this first text paragraph
                if pending_before > 0:
                    current_before = style["space_before"] if style["space_before"] is not None else 0
                    style["space_before"] = current_before + pending_before
                    pending_before = 0
                last_text_idx = i
            else:
                # Calculate visual height of this empty paragraph
                # Default font size 18pt if missing (approximate)
                f_size = 18 * 12700 
                if style["font_obj"] and style["font_obj"].size:
                    f_size = style["font_obj"].size
                
                # Default line spacing 1.0 lines
                l_spacing = 1.0
                is_spacing_points = False
                if style["line_spacing"]:
                    if isinstance(style["line_spacing"], int) or style["line_spacing"] > 100: 
                        # It's likely points/EMUs
                        l_spacing = style["line_spacing"]
                        is_spacing_points = True
                    else:
                        l_spacing = style["line_spacing"]
                
                # Approximate height
                if is_spacing_points:
                    para_height = l_spacing
                else:
                    para_height = int(f_size * l_spacing)
                
                # Add extra spacing from space_before/after of the empty paragraph itself
                p_before = style["space_before"] if style["space_before"] else 0
                p_after = style["space_after"] if style["space_after"] else 0
                total_empty_height = para_height + p_before + p_after

                if last_text_idx >= 0:
                    # Add to previous paragraph's space_after
                    prev_after = styles[last_text_idx]["space_after"] if styles[last_text_idx]["space_after"] is not None else 0
                    styles[last_text_idx]["space_after"] = prev_after + total_empty_height
                else:
                    # Accumulate for the first upcoming text paragraph
                    pending_before += total_empty_height

    except Exception: pass
    
    return styles

def apply_paragraph_style(
    paragraph, 
    p_style: dict[str, Any], 
    scale: float = 1.0, 
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None
) -> None:
    try:
        # Step 1: High-fidelity XML sync for Indents and Bullets (Base State)
        p_pr_xml_bytes = p_style.get("pPr_xml")
        if p_pr_xml_bytes:
            try:
                target_p = paragraph._p
                new_p_pr = etree.fromstring(p_pr_xml_bytes)
                
                # Replace or update existing pPr
                old_p_pr = target_p.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}pPr')
                if old_p_pr is None:
                    old_p_pr = target_p.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}pPr')
                
                if old_p_pr is not None:
                    target_p.replace(old_p_pr, new_p_pr)
                else:
                    target_p.insert(0, new_p_pr)
            except Exception: pass

        # Step 2: Apply basic properties via API (Overrides)
        # This must come AFTER XML sync so our calculated spacing takes precedence
        paragraph.level = p_style.get("level", 0)
        paragraph.alignment = p_style.get("alignment")
        if p_style.get("space_before") is not None: paragraph.space_before = p_style["space_before"]
        if p_style.get("space_after") is not None: paragraph.space_after = p_style["space_after"]
        if p_style.get("line_spacing") is not None: paragraph.line_spacing = p_style["line_spacing"]
            
        # Step 3: Font properties
        source_font = p_style.get("font_obj")
        if source_font and paragraph.runs:
            clone_font_props(source_font, paragraph.runs[0].font, target_language=target_language, font_mapping=font_mapping)
            if scale != 1.0 and paragraph.runs[0].font.size:
                paragraph.runs[0].font.size = int(paragraph.runs[0].font.size * scale)
    except Exception: pass
