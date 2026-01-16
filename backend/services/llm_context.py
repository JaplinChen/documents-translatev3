from __future__ import annotations


def build_context(strategy: str, all_blocks: list[dict], chunk_blocks: list[dict]) -> dict | None:
    if strategy == "none":
        return None

    blocks_by_slide: dict[int, list[dict]] = {}
    for block in all_blocks:
        slide_index = block.get("slide_index")
        if slide_index is None:
            continue
        blocks_by_slide.setdefault(slide_index, []).append(block)

    chunk_slides = {block.get("slide_index") for block in chunk_blocks}
    if strategy == "neighbor":
        context_blocks = []
        for slide_index in chunk_slides:
            if slide_index is None:
                continue
            for neighbor in (slide_index - 1, slide_index, slide_index + 1):
                context_blocks.extend(blocks_by_slide.get(neighbor, []))
        return {"strategy": "neighbor", "context_blocks": context_blocks}

    if strategy == "title-only":
        title_blocks = []
        for slide_index in chunk_slides:
            if slide_index is None:
                continue
            slide_blocks = blocks_by_slide.get(slide_index, [])
            if slide_blocks:
                title_blocks.append(slide_blocks[0])
        return {"strategy": "title-only", "context_blocks": title_blocks}

    if strategy == "deck":
        deck_blocks = []
        for slide_index in sorted(blocks_by_slide.keys())[:2]:
            deck_blocks.extend(blocks_by_slide.get(slide_index, []))
        return {"strategy": "deck", "context_blocks": deck_blocks}

    return None
