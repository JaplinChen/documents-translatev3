from __future__ import annotations

from fastapi import APIRouter, Response

from backend.services.translation_memory_adapter import list_learning_events, list_learning_stats

router = APIRouter()


@router.get("/learning-events")
async def tm_learning_events(
    limit: int = 200,
    offset: int = 0,
    event_type: str | None = None,
    entity_type: str | None = None,
    scope_type: str | None = None,
    scope_id: str | None = None,
    source_lang: str | None = None,
    target_lang: str | None = None,
    q: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> dict:
    items, total = list_learning_events(
        limit=limit,
        offset=offset,
        event_type=event_type,
        entity_type=entity_type,
        scope_type=scope_type,
        scope_id=scope_id,
        source_lang=source_lang,
        target_lang=target_lang,
        q=q,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/learning-stats")
async def tm_learning_stats(
    limit: int = 30,
    offset: int = 0,
    scope_type: str | None = None,
    scope_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> dict:
    items, total = list_learning_stats(
        limit=limit,
        offset=offset,
        scope_type=scope_type,
        scope_id=scope_id,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/learning-events/export")
async def tm_learning_events_export(
    event_type: str | None = None,
    entity_type: str | None = None,
    scope_type: str | None = None,
    scope_id: str | None = None,
    source_lang: str | None = None,
    target_lang: str | None = None,
    q: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> Response:
    items, _ = list_learning_events(
        limit=1000,
        offset=0,
        event_type=event_type,
        entity_type=entity_type,
        scope_type=scope_type,
        scope_id=scope_id,
        source_lang=source_lang,
        target_lang=target_lang,
        q=q,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    lines = [
        "id,created_at,event_type,entity_type,entity_id,source_lang,target_lang,source_text,target_text,scope_type,scope_id"
    ]
    for item in items:
        lines.append(
            f"{item.get('id')},{item.get('created_at')},{item.get('event_type')},"
            f"{item.get('entity_type')},{item.get('entity_id')},"
            f"{item.get('source_lang')},{item.get('target_lang')},"
            f"{item.get('source_text')},{item.get('target_text')},"
            f"{item.get('scope_type')},{item.get('scope_id')}"
        )
    return Response(content="\n".join(lines), media_type="text/csv")


@router.get("/learning-stats/export")
async def tm_learning_stats_export(
    scope_type: str | None = None,
    scope_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> Response:
    items, _ = list_learning_stats(
        limit=365,
        offset=0,
        scope_type=scope_type,
        scope_id=scope_id,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    lines = [
        "id,stat_date,tm_hit_rate,glossary_hit_rate,overwrite_rate,auto_promotion_error_rate,wrong_suggestion_rate,scope_type,scope_id,created_at"
    ]
    for item in items:
        lines.append(
            f"{item.get('id')},{item.get('stat_date')},{item.get('tm_hit_rate')},"
            f"{item.get('glossary_hit_rate')},{item.get('overwrite_rate')},"
            f"{item.get('auto_promotion_error_rate')},{item.get('wrong_suggestion_rate')},"
            f"{item.get('scope_type')},{item.get('scope_id')},{item.get('created_at')}"
        )
    return Response(content="\n".join(lines), media_type="text/csv")
