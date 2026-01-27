"""
PPTX Slide Utilities - Slide duplication and insertion helpers.
"""

from __future__ import annotations

import logging
import random
from copy import deepcopy

from pptx import Presentation
from pptx.slide import Slide

logger = logging.getLogger(__name__)


def duplicate_slide(
    presentation: Presentation, slide: Slide
) -> tuple[Slide, dict[int, int]]:
    """Create a high-fidelity copy of the provided slide."""
    try:
        logger.debug(
            "Duplicating slide with %s shapes",
            len(slide.shapes),
        )

        new_slide = presentation.slides.add_slide(slide.slide_layout)
        for shape in list(new_slide.shapes):
            try:
                shape.element.getparent().remove(shape.element)
            except Exception as err:  # pragma: no cover
                logger.debug("Could not clear placeholder: %s", err)

        shape_id_map: dict[int, int] = {}
        base_id = random.randint(10_000, 99_999_999)
        p_ns = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
        a_ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

        rid_mapping: dict[str, str] = {}
        for rel in slide.part.rels.values():
            if (
                rel.reltype.endswith("slideLayout")
                or rel.reltype.endswith("notesSlide")
                or rel.reltype.endswith("master")
            ):
                continue
            old_rid = rel.rId
            try:
                new_rid = (
                    new_slide.part.relate_to(
                        rel.target_ref, rel.reltype, is_external=True
                    )
                    if rel.is_external
                    else new_slide.part.relate_to(rel.target_part, rel.reltype)
                )
                rid_mapping[old_rid] = new_rid
            except Exception as err:  # pragma: no cover
                logger.debug(
                    "Failed to copy relationship %s: %s",
                    old_rid,
                    err,
                )

        sp_tree = new_slide.shapes._spTree
        ext_lst = sp_tree.find(f"{p_ns}extLst")

        for shape in slide.shapes:
            try:
                new_element = deepcopy(shape.element)
                _regenerate_ids(new_element, base_id, shape_id_map)
                _rewrite_references(
                    new_element,
                    a_ns,
                    rid_mapping,
                    shape_id_map,
                )
                if ext_lst is not None:
                    ext_lst.addprevious(new_element)
                else:
                    sp_tree.append(new_element)
            except Exception as err:  # pragma: no cover
                logger.debug(
                    "Failed to duplicate shape %s: %s", shape.shape_id, err
                )
                continue

        return new_slide, shape_id_map
    except Exception:  # pragma: no cover
        logger.exception("duplicate_slide failed, falling back to blank slide")
        fallback = presentation.slides.add_slide(presentation.slide_layouts[6])
        return fallback, {}


def _regenerate_ids(
    element,
    base_id: int,
    shape_id_map: dict[int, int],
) -> None:
    for child in element.iter():
        if child.tag.endswith("}cNvPr"):
            current_id = child.get("id")
            if current_id and current_id.isdigit():
                old_sid = int(current_id)
                shape_id_map[old_sid] = base_id + len(shape_id_map)
                child.set("id", str(shape_id_map[old_sid]))


def _rewrite_references(
    element,
    a_ns: str,
    rid_mapping: dict[str, str],
    shape_id_map: dict[int, int],
) -> None:
    for child in element.iter():
        if child.tag in (f"{a_ns}stCxn", f"{a_ns}endCxn"):
            ref_id = child.get("id")
            if ref_id and ref_id.isdigit():
                mapped = shape_id_map.get(int(ref_id))
                if mapped:
                    child.set("id", str(mapped))
        for attr_name, attr_value in list(child.attrib.items()):
            if "relationships" in attr_name and attr_value in rid_mapping:
                child.attrib[attr_name] = rid_mapping[attr_value]


def insert_slide_after(
    presentation: Presentation, new_slide: Slide, after_index: int
) -> None:
    """Insert slide reference after provided index."""
    sld_id_list = presentation.slides._sldIdLst
    new_sld_id = sld_id_list[-1]
    sld_id_list.remove(new_sld_id)
    sld_id_list.insert(after_index + 1, new_sld_id)
