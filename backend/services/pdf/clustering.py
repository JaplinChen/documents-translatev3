import logging

LOGGER = logging.getLogger(__name__)


def cluster_blocks(
    blocks: list[dict],
    line_spacing_threshold: float = 1.5,
    x_overlap_threshold: float = 0.5,
) -> list[dict]:
    """Cluster PDF text blocks into paragraphs based on proximity."""
    if not blocks:
        return []

    # Group by page
    pages = {}
    for b in blocks:
        idx = b["slide_index"]
        if idx not in pages:
            pages[idx] = []
        pages[idx].append(b)

    clustered_all = []

    for page_idx in sorted(pages.keys()):
        page_blocks = sorted(
            pages[page_idx],
            key=lambda b: (b["y"], b["x"]),
        )
        if not page_blocks:
            continue

        merged_page = []
        current = page_blocks[0].copy()

        for next_block in page_blocks[1:]:
            # Ensure all required coordinates are present and not None
            curr_y = current.get("y", 0.0) or 0.0
            curr_h = current.get("height", 0.0) or 0.0
            next_y = next_block.get("y", 0.0) or 0.0
            next_h = next_block.get("height", 0.0) or 0.0

            curr_bottom = curr_y + curr_h
            next_top = next_y

            # Estimate font size (use current height if not provided or None)
            font_size = current.get("font_size")
            if font_size is None:
                font_size = curr_h
            if font_size == 0:
                font_size = 10.0  # Default fallback

            v_dist = next_top - curr_bottom

            # Alignment check: horizontal overlap or similar starting X
            curr_x0 = current.get("x", 0.0) or 0.0
            curr_w = current.get("width", 0.0) or 0.0
            next_x0 = next_block.get("x", 0.0) or 0.0
            next_w = next_block.get("width", 0.0) or 0.0

            curr_x1 = curr_x0 + curr_w
            next_x1 = next_x0 + next_w

            x_overlap = min(curr_x1, next_x1) - max(curr_x0, next_x0)
            is_aligned = (abs(curr_x0 - next_x0) < 10) or (x_overlap > 0)

            # Merge if close and aligned
            if (
                v_dist < (font_size * line_spacing_threshold)
                and v_dist > -5
                and is_aligned
            ):
                # Merge text
                current["source_text"] += " " + next_block["source_text"]
                # Update bounding box
                new_x = min(curr_x0, next_x0)
                new_y = min(curr_y, next_y)
                new_x1 = max(curr_x1, next_x1)
                new_y1 = max(curr_bottom, next_y + next_h)

                current["x"] = new_x
                current["y"] = new_y
                current["width"] = new_x1 - new_x
                current["height"] = new_y1 - new_y

                # Update metadata (prefer original if conflicting)
                current["is_merged"] = True
            else:
                merged_page.append(current)
                current = next_block.copy()

        merged_page.append(current)
        clustered_all.extend(merged_page)

    return clustered_all
