from __future__ import annotations

from fastapi import APIRouter

from backend.services.term_repository import sync_from_external

router = APIRouter()


@router.post("/sync-all")
async def term_sync_all() -> dict:
    """Synchronize all existing data from preserve_terms and glossary to terms center."""
    from backend.services.preserve_terms_repository import list_preserve_terms
    from backend.services.translation_memory_adapter import get_glossary

    synced_count = 0
    p_terms = list_preserve_terms()
    for pt in p_terms:
        try:
            case_rule = "uppercase" if pt.get("case_sensitive") else "preserve"
            sync_from_external(
                pt["term"],
                category_name=pt.get("category"),
                source="terminology",
                case_rule=case_rule,
            )
            synced_count += 1
        except Exception as exc:
            print(f"Sync sync-all preserve failed for {pt['term']}: {exc}")

    g_terms = get_glossary(limit=5000)
    for gt in g_terms:
        try:
            lang_code = gt.get("target_lang", "zh-TW")
            sync_from_external(
                gt["source_text"],
                category_name=gt.get("category_name"),
                source="reference",
                source_lang=gt.get("source_lang"),
                target_lang=gt.get("target_lang"),
                priority=gt.get("priority", 0),
                languages=[{"lang_code": lang_code, "value": gt["target_text"]}],
            )
            synced_count += 1
        except Exception as exc:
            print(f"Sync sync-all glossary failed for {gt['source_text']}: {exc}")

    return {"status": "ok", "synced": synced_count}
