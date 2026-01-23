import logging
import uuid
from backend.services.language_detect import detect_language

LOGGER = logging.getLogger(__name__)

def align_bilingual_blocks(blocks: list[dict], source_lang: str, target_lang: str) -> list[dict]:
    """
    Analyzes a sequence of blocks and marks [Source, Target] pairs for alignment.
    """
    if not source_lang or not target_lang or source_lang == "auto" or target_lang == "auto":
        return blocks

    processed = []
    i = 0
    n = len(blocks)
    
    while i < n:
        curr = blocks[i]
        curr_text = curr.get("source_text", "").strip()
        if not curr_text:
            processed.append(curr)
            i += 1
            continue
            
        curr_lang = detect_language(curr_text)
        LOGGER.info("[ALIGN] Block %d: lang=%s, text_prefix=%s", i, curr_lang, curr_text[:20])
        
        # Check for pair: current is source_lang (or VI misdetected), next is target_lang
        if i + 1 < n:
            next_block = blocks[i+1]
            next_text = next_block.get("source_text", "").strip()
            next_lang = detect_language(next_text)
            
            # Robust pair detection:
            # 1. source_lang followed by target_lang
            # 2. Both are target_lang (often happens if VI is misdetected as ZH)
            is_pair = (curr_lang == source_lang and next_lang == target_lang) or \
                      (curr_lang == target_lang and next_lang == target_lang)
            
            if is_pair:
                pair_id = str(uuid.uuid4())[:8]
                LOGGER.info("[ALIGN] Detected potential bilingual pair %s at indices (%d, %d)", pair_id, i, i+1)
                
                # Mark source block
                source_meta = dict(curr)
                source_meta["alignment_role"] = "source"
                source_meta["alignment_pair_id"] = pair_id
                
                # Mark target block
                target_meta = dict(next_block)
                target_meta["alignment_role"] = "target"
                target_meta["alignment_pair_id"] = pair_id
                target_meta["alignment_source"] = curr_text
                
                processed.append(source_meta)
                processed.append(target_meta)
                i += 2
                continue
                
        processed.append(curr)
        i += 1
        
    return processed
