from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

import httpx

from backend.config import settings
from backend.services.llm_contract import build_contract
from backend.services.llm_utils import chunked
from backend.services.translate_llm_helpers import create_async_chunk_tasks

from .chunk import _finalize_texts, _translate_chunk_sync
from .context import prepare_translation_context

LOGGER = logging.getLogger(__name__)


def translate_blocks(
    blocks: list[dict],
    target_language: str,
    source_language: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    use_tm: bool = True,
    tone: str | None = None,
    vision_context: bool = True,
    smart_layout: bool = True,
    scope_type: str | None = None,
    scope_id: str | None = None,
    domain: str | None = None,
    category: str | None = None,
    param_overrides: dict | None = None,
    mode: str | None = None,
) -> dict:
    ctx = prepare_translation_context(
        blocks,
        target_language,
        source_language,
        provider,
        model,
        api_key,
        base_url,
        use_tm,
        tone,
        vision_context,
        scope_type,
        scope_id,
        domain,
        category,
        param_overrides,
        mode,
    )

    LOGGER.info(
        "LLM translate start provider=%s model=%s blocks=%s chunk=%s",
        ctx["resolved_provider"],
        model or "",
        len(ctx["blocks_list"]),
        ctx["chunk_size"],
    )

    for chunk_index, chunk in enumerate(chunked(ctx["pending"], ctx["chunk_size"]), start=1):
        chunk_started = time.perf_counter()
        _translate_chunk_sync(
            ctx["translator"],
            ctx["resolved_provider"],
            chunk,
            target_language,
            ctx["blocks_list"],
            ctx["params"],
            ctx["preferred_terms"],
            tone,
            vision_context,
            ctx["fallback_on_error"],
            ctx["resolved_mode"],
            ctx["use_placeholders"],
            ctx["llm_context"],
            ctx["translated_texts"],
            ctx["local_cache"],
            ctx["glossary"],
            use_tm,
            chunk_index,
        )
        chunk_duration = time.perf_counter() - chunk_started
        LOGGER.info(
            "LLM chunk %s completed in %.2fs",
            chunk_index,
            chunk_duration,
        )
        if ctx["params"]["chunk_delay"]:
            time.sleep(ctx["params"]["chunk_delay"])

    final_texts = _finalize_texts(ctx["blocks_list"], ctx["translated_texts"])
    return build_contract(
        blocks=ctx["blocks_list"],
        translated_texts=final_texts,
        target_language=target_language,
    )


async def translate_blocks_async(
    blocks: list[dict],
    target_language: str,
    source_language: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    use_tm: bool = True,
    tone: str | None = None,
    vision_context: bool = True,
    smart_layout: bool = True,
    scope_type: str | None = None,
    scope_id: str | None = None,
    domain: str | None = None,
    category: str | None = None,
    param_overrides: dict | None = None,
    on_progress: Callable[[dict], Any] | None = None,
    mode: str | None = None,
) -> dict:
    ctx = prepare_translation_context(
        blocks,
        target_language,
        source_language,
        provider,
        model,
        api_key,
        base_url,
        use_tm,
        tone,
        vision_context,
        scope_type,
        scope_id,
        domain,
        category,
        param_overrides,
        mode,
    )

    LOGGER.info(
        "LLM translate start async provider=%s model=%s blocks=%s chunk=%s",
        ctx["resolved_provider"],
        model or "",
        len(ctx["blocks_list"]),
        ctx["chunk_size"],
    )

    chunk_list = list(chunked(ctx["pending"], ctx["chunk_size"]))
    tasks = create_async_chunk_tasks(
        chunk_list,
        ctx["translator"],
        ctx["resolved_provider"],
        ctx["blocks_list"],
        target_language,
        ctx["preferred_terms"],
        ctx["use_placeholders"],
        ctx["params"],
        ctx["fallback_on_error"],
        ctx["resolved_mode"],
        ctx["translated_texts"],
        ctx["local_cache"],
        ctx["glossary"],
        use_tm,
        tone,
        vision_context,
        on_progress,
        llm_context=ctx["llm_context"],
    )

    if tasks:
        if settings.llm_max_concurrency > 0:
            sem_val = settings.llm_max_concurrency
        else:
            sem_val = 1 if ctx["resolved_provider"] == "ollama" else 5

        sem = asyncio.Semaphore(sem_val)

        async def sem_wrapped_task(task):
            async with sem:
                try:
                    return await asyncio.wait_for(task, timeout=settings.llm_request_timeout)
                except asyncio.TimeoutError:
                    LOGGER.error("LLM Task timed out after %ss", settings.llm_request_timeout)
                    return None
                except Exception as exc:
                    LOGGER.error("LLM Task failed: %s", exc)
                    return None

        final_tasks = [sem_wrapped_task(t) for t in tasks]

        if hasattr(ctx["translator"], "set_async_client"):
            total_timeout = httpx.Timeout(settings.ollama_timeout, connect=10.0)
            async with httpx.AsyncClient(timeout=total_timeout) as client:
                ctx["translator"].set_async_client(client)
                await asyncio.gather(*final_tasks)
        else:
            await asyncio.gather(*final_tasks)

    final_texts = [text if text is not None else "" for text in ctx["translated_texts"]]

    for i, block in enumerate(ctx["blocks_list"]):
        if block.get("alignment_role") == "source":
            final_texts[i] = block.get("source_text", "")

    return build_contract(
        blocks=ctx["blocks_list"],
        translated_texts=final_texts,
        target_language=target_language,
    )
