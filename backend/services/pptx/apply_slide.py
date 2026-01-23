"""
PPTX Slide Utilities - Slide duplication and insertion functions.
Extracted from pptx_apply_layout.py for modularity.
"""
from __future__ import annotations

import random
from copy import deepcopy

from pptx import Presentation
from pptx.slide import Slide


def duplicate_slide(presentation: Presentation, slide: Slide) -> tuple[Slide, dict[int, int]]:
    """
    Duplicate a slide with full fidelity including images and shapes.
    
    Uses a hybrid approach:
    - Pictures are re-added using add_picture() with extracted blob data
    - Other shapes are XML-copied with ID regeneration
    
    Returns:
        tuple: (new_slide, shape_id_map) where shape_id_map maps old shape IDs to new shape IDs.
    """
    try:
        print(f"[HYBRID_DUP] Starting duplicate_slide for slide with {len(slide.shapes)} shapes", flush=True)
        
        # 1. Create a new slide based on the same layout
        new_slide = presentation.slides.add_slide(slide.slide_layout)
        
        # Clear any default layout shapes (we'll copy everything from source)
        for shape in list(new_slide.shapes):
            try:
                el = shape.element
                el.getparent().remove(el)
            except Exception as e:
                print(f"[HYBRID_DUP] Failed to clear placeholder: {e}", flush=True)
                pass
        
        shape_id_map = {}
        base_id = random.randint(10000, 99999999)
        id_counter = 0
        
        # Namespaces
        p_ns = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
        a_ns = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
        
        # 2. Copy relationships (excluding layout and master)
        rid_mapping = {}
        for rel in slide.part.rels.values():
            if rel.reltype in (
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/master"
            ):
                continue
            
            old_rid = rel.rId
            try:
                if rel.is_external:
                    new_rid = new_slide.part.relate_to(rel.target_ref, rel.reltype, is_external=True)
                else:
                    new_rid = new_slide.part.relate_to(rel.target_part, rel.reltype)
                
                rid_mapping[old_rid] = new_rid
            except Exception as e:
                print(f"[XML_DUP] Failed to copy relationship {old_rid} ({rel.reltype}): {e}", flush=True)
        
        # 3. Process each shape
        sp_tree = new_slide.shapes._spTree
        ext_lst = sp_tree.find(f"{p_ns}extLst")
        
        for shape in slide.shapes:
            try:
                # Use unified XML deep copy for ALL shapes
                new_element = deepcopy(shape.element)
                
                # Pass 1: Regenerate all shape IDs
                for elem in new_element.iter():
                    if elem.tag.endswith('}cNvPr'):
                        try:
                            current_id = elem.get('id')
                            if current_id:
                                old_sid = int(current_id)
                                new_id = base_id + id_counter
                                id_counter += 1
                                elem.set('id', str(new_id))
                                shape_id_map[old_sid] = new_id
                        except ValueError:
                            pass
                
                # Pass 2: Fix references (Connectors and Relationships)
                for elem in new_element.iter():
                    # Fix connector references
                    if elem.tag in (f"{a_ns}stCxn", f"{a_ns}endCxn"):
                        ref_id = elem.get('id')
                        if ref_id and ref_id.isdigit():
                            rid_int = int(ref_id)
                            if rid_int in shape_id_map:
                                elem.set('id', str(shape_id_map[rid_int]))
                    
                    # Fix relationship references (r:id, r:embed, r:link, etc.)
                    for attr_name, attr_val in list(elem.attrib.items()):
                        if 'http://schemas.openxmlformats.org/officeDocument/2006/relationships' in attr_name:
                            if attr_val in rid_mapping:
                                elem.attrib[attr_name] = rid_mapping[attr_val]
                
                # Insert into shape tree
                if ext_lst is not None:
                    ext_lst.addprevious(new_element)
                else:
                    sp_tree.append(new_element)
                    
            except Exception as e:
                print(f"[HYBRID_DUP] Failed to copy shape ID {shape.shape_id}: {e}", flush=True)
                continue
        
        return new_slide, shape_id_map

    except Exception as exc:
        print(f"[HYBRID_DUP] CRITICAL: duplicate_slide completely failed. Falling back to Blank slide. Error: {exc}", flush=True)
        return presentation.slides.add_slide(presentation.slide_layouts[6]), {}


def insert_slide_after(presentation: Presentation, new_slide: Slide, after_index: int) -> None:
    """Insert a slide after a specific index in the presentation."""
    sld_id_list = presentation.slides._sldIdLst
    new_sld_id = sld_id_list[-1]
    sld_id_list.remove(new_sld_id)
    sld_id_list.insert(after_index + 1, new_sld_id)
