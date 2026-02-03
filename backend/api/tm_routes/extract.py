from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.api.tm_routes.models import GlossaryExtractPayload

router = APIRouter()


@router.post("/extract-glossary")
async def tm_extract_glossary(payload: GlossaryExtractPayload) -> dict:
    """
    Unified terminology extraction for all file types (PPTX, DOCX, XLSX).
    Uses JSON instead of Form for stability with large block lists.
    """
    from backend.services.glossary_extraction import extract_glossary_terms

    try:
        result = extract_glossary_terms(
            payload.blocks,
            payload.target_language,
            provider=payload.provider,
            model=payload.model,
            api_key=payload.api_key,
            base_url=payload.base_url,
        )
        return result
    except Exception as exc:
        import traceback

        traceback.print_exc()
        return {"terms": [], "error": str(exc)}


@router.post("/extract-glossary-stream")
async def tm_extract_glossary_stream(payload: GlossaryExtractPayload) -> StreamingResponse:
    """
    Streaming version of terminology extraction.
    Reports progress via SSE while analyzing document segments.
    """
    from backend.services.glossary_extraction import extract_glossary_terms
    import asyncio
    import json

    async def event_generator():
        try:
            blocks = payload.blocks
            total_blocks = len(blocks)

            segments = []
            if total_blocks <= 20:
                segments = [blocks]
            else:
                chunk_size = min(20, total_blocks // 3) if total_blocks > 0 else 0
                if chunk_size > 0:
                    segments.append(blocks[:chunk_size])
                    mid = total_blocks // 2
                    segments.append(blocks[mid : mid + chunk_size])
                    segments.append(blocks[-chunk_size:])
                else:
                    segments = [blocks]

            all_terms = []
            num_segments = len(segments)

            yield f"event: progress\ndata: {json.dumps({'message': '正在準備分析文本...', 'percent': 10})}\n\n"
            await asyncio.sleep(0.1)

            for i, segment in enumerate(segments):
                stage_name = f"正在分析第 {i + 1}/{num_segments} 段文本..."
                percent = int(10 + (i / num_segments) * 80)
                yield f"event: progress\ndata: {json.dumps({'message': stage_name, 'percent': percent})}\n\n"

                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    extract_glossary_terms,
                    segment,
                    payload.target_language,
                    payload.provider,
                    payload.model,
                    payload.api_key,
                    payload.base_url,
                )

                terms = result.get("terms", [])
                domain = result.get("domain", "general")

                if terms and isinstance(terms, list):
                    all_terms.extend(terms)

            unique_terms_map = {}
            for term in all_terms:
                if not isinstance(term, dict) or "source" not in term:
                    continue
                key = term["source"].strip().lower()
                if key not in unique_terms_map:
                    unique_terms_map[key] = term

            final_terms = list(unique_terms_map.values())

            yield f"event: progress\ndata: {json.dumps({'message': '完成分析，正在彙整術語...', 'percent': 95})}\n\n"
            await asyncio.sleep(0.5)

            payload_data = {"terms": final_terms, "domain": domain}
            yield f"event: complete\ndata: {json.dumps(payload_data)}\n\n"

        except Exception as exc:
            import traceback

            traceback.print_exc()
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
