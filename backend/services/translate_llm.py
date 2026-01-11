from __future__ import annotations

import json
import os
import csv
import time
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen

from backend.services.translation_memory import (
    get_glossary_terms,
    get_glossary_terms_any,
    get_tm_terms,
    get_tm_terms_any,
    lookup_tm,
    save_tm,
)

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "translation_contract_pptx.json"
)


def _load_contract_example() -> dict:
    if not CONTRACT_PATH.exists():
        raise FileNotFoundError(f"Missing contract file: {CONTRACT_PATH}")
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class TranslationConfig:
    model: str
    api_key: str
    base_url: str


class MockTranslator:
    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
    ) -> dict:
        return _build_contract(blocks, target_language, translated_texts=None)


class OpenAITranslator:
    def __init__(self, config: TranslationConfig) -> None:
        self.config = config

    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
    ) -> dict:
        contract_example = _load_contract_example()
        prompt = _build_prompt(
            blocks,
            target_language,
            contract_example,
            context,
            preferred_terms,
            placeholder_tokens,
        )
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You translate PPTX text blocks. "
                        "Return only JSON and match the provided schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.config.base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        content = response_data["choices"][0]["message"]["content"]
        result = json.loads(content)
        _validate_contract(result)
        return result


class GeminiTranslator:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
    ) -> dict:
        contract_example = _load_contract_example()
        prompt = _build_prompt(
            blocks,
            target_language,
            contract_example,
            context,
            preferred_terms,
            placeholder_tokens,
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "response_mime_type": "application/json"},
        }
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        candidates = response_data.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates returned from Gemini")
        parts = candidates[0].get("content", {}).get("parts", [])
        content = parts[0].get("text", "") if parts else ""
        result = _safe_json_loads(content)
        _validate_contract(result)
        return result


class OllamaTranslator:
    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
    ) -> dict:
        contract_example = _load_contract_example()
        prompt = _build_prompt(
            blocks,
            target_language,
            contract_example,
            context,
            preferred_terms,
            placeholder_tokens,
        )
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You translate PPTX text blocks. "
                        "Return only JSON and match the provided schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        content = response_data.get("message", {}).get("content", "")
        result = json.loads(content)
        _validate_contract(result)
        return result


def _build_contract(
    blocks: Iterable[dict],
    target_language: str,
    translated_texts: Iterable[str] | None,
) -> dict:
    output_blocks = []
    translated_iter = iter(translated_texts) if translated_texts is not None else None
    for block in blocks:
        translated_text = (
            next(translated_iter) if translated_iter is not None else block.get("source_text", "")
        )
        output_blocks.append(
            {
                "slide_index": block.get("slide_index"),
                "shape_id": block.get("shape_id"),
                "block_type": block.get("block_type"),
                "source_text": block.get("source_text", ""),
                "translated_text": translated_text,
            }
        )
    return {
        "document_language": "auto",
        "target_language": target_language,
        "blocks": output_blocks,
    }


def _build_prompt(
    blocks: Iterable[dict],
    target_language: str,
    contract_example: dict,
    context: dict | None,
    preferred_terms: list[tuple[str, str]] | None = None,
    placeholder_tokens: list[str] | None = None,
) -> str:
    input_payload = {
        "target_language": target_language,
        "blocks": list(blocks),
        "contract_schema_example": contract_example,
    }
    if preferred_terms:
        input_payload["preferred_terms"] = [
            {"source": source, "target": target} for source, target in preferred_terms
        ]
    if placeholder_tokens:
        input_payload["placeholder_tokens"] = placeholder_tokens
    if context:
        input_payload["context"] = context
    return (
        "Translate each block into the target_language. "
        "Always prioritize preferred_terms if provided. "
        "Never translate or alter placeholder_tokens if provided. "
        "Keep line breaks as \\n and do not add extra fields. "
        "Return JSON matching contract_schema_example with a top-level 'blocks' list.\n\n"
        f"{json.dumps(input_payload, ensure_ascii=True)}"
    )


def _apply_placeholders(
    text: str, terms: list[tuple[str, str]]
) -> tuple[str, dict[str, str]]:
    if not text or not terms:
        return text, {}
    term_map = {}
    updated = text
    sorted_terms = sorted(terms, key=lambda item: len(item[0]), reverse=True)
    for idx, (source, target) in enumerate(sorted_terms):
        if not source:
            continue
        token = f"__TERM_{idx}__"
        pattern = re.compile(re.escape(source), re.IGNORECASE)
        if pattern.search(updated):
            updated = pattern.sub(token, updated)
            term_map[token] = target
    return updated, term_map


def _restore_placeholders(text: str, mapping: dict[str, str]) -> str:
    if not text or not mapping:
        return text
    updated = text
    for token, target in mapping.items():
        updated = updated.replace(token, target)
    return updated


def _tm_respects_terms(
    source_text: str, translated_text: str, preferred_terms: list[tuple[str, str]]
) -> bool:
    if not source_text or not translated_text or not preferred_terms:
        return True
    for source, target in preferred_terms:
        if not source or not target:
            continue
        if source.lower() in source_text.lower() and target not in translated_text:
            return False
    return True


def _validate_contract(result: dict) -> None:
    if "blocks" not in result:
        raise ValueError("Missing blocks in LLM response")
    for block in result["blocks"]:
        for key in ("slide_index", "shape_id", "block_type", "source_text", "translated_text"):
            if key not in block:
                raise ValueError(f"Missing {key} in LLM response block")


def _safe_json_loads(content: str) -> dict:
    if not content:
        raise ValueError("Empty LLM response content")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1])
        raise ValueError("LLM response is not valid JSON")


def _coerce_contract(result: dict, blocks: list[dict], target_language: str) -> dict:
    if isinstance(result, dict) and "blocks" in result:
        return result

    candidate_list = None
    if isinstance(result, list):
        candidate_list = result
    elif isinstance(result, dict):
        for key in ("translations", "data", "items", "results", "output"):
            value = result.get(key)
            if isinstance(value, list):
                candidate_list = value
                break

    if candidate_list is None:
        return {"blocks": []}

    if candidate_list and all(isinstance(item, str) for item in candidate_list):
        return _build_contract(blocks, target_language, candidate_list)

    if candidate_list and all(isinstance(item, dict) for item in candidate_list):
        translated_texts = []
        for item in candidate_list:
            translated_texts.append(
                item.get("translated_text")
                or item.get("translation")
                or item.get("text")
                or ""
            )
        return _build_contract(blocks, target_language, translated_texts)

    return result


def _cache_key(block: dict) -> str:
    return block.get("source_text", "").strip()


def _chunked(items: list[tuple[int, dict]], size: int) -> Iterable[list[tuple[int, dict]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _load_glossary(path: str | None) -> list[tuple[str, str]]:
    if not path:
        return []
    entries: list[tuple[str, str]] = []
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            source = row[0].strip()
            target = row[1].strip()
            if source:
                entries.append((source, target))
    return entries


def _apply_glossary(text: str, glossary: list[tuple[str, str]]) -> str:
    updated = text
    for source, target in glossary:
        updated = updated.replace(source, target)
    return updated


def _build_context(strategy: str, all_blocks: list[dict], chunk_blocks: list[dict]) -> dict | None:
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


def translate_blocks(
    blocks: Iterable[dict],
    target_language: str,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict:
    mode = os.getenv("TRANSLATE_LLM_MODE", "mock").lower()
    resolved_provider = (provider or "openai").lower()

    if mode == "mock" and provider is None:
        translator = MockTranslator()
    elif resolved_provider in {"openai", "chatgpt"}:
        resolved_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not resolved_key:
            raise EnvironmentError("OPENAI_API_KEY is required for OpenAI translation")
        config = TranslationConfig(
            model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=resolved_key,
            base_url=base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        translator = OpenAITranslator(config)
    elif resolved_provider == "gemini":
        resolved_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not resolved_key:
            raise EnvironmentError("GEMINI_API_KEY is required for Gemini translation")
        translator = GeminiTranslator(
            api_key=resolved_key,
            base_url=base_url
            or os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
            model=model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        )
    elif resolved_provider == "ollama":
        resolved_model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        translator = OllamaTranslator(
            model=resolved_model,
            base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    else:
        translator = MockTranslator()

    blocks_list = list(blocks)
    cache: dict[str, str] = {}
    translated_texts: list[str | None] = [None] * len(blocks_list)
    pending: list[tuple[int, dict]] = []
    source_lang = os.getenv("SOURCE_LANGUAGE", "auto")
    preferred_terms: list[tuple[str, str]] = []
    if source_lang and source_lang != "auto":
        preferred_terms = get_glossary_terms(source_lang, target_language)
        preferred_terms.extend(get_tm_terms(source_lang, target_language))
    else:
        preferred_terms = get_glossary_terms_any(target_language)
        preferred_terms.extend(get_tm_terms_any(target_language))

    for index, block in enumerate(blocks_list):
        key = _cache_key(block)
        if not key:
            translated_texts[index] = ""
            continue
        if key in cache:
            translated_texts[index] = cache[key]
            continue
        if source_lang and source_lang != "auto":
            tm_hit = lookup_tm(
                source_lang=source_lang,
                target_lang=target_language,
                text=key,
            )
            if tm_hit is not None and _tm_respects_terms(key, tm_hit, preferred_terms):
                translated_texts[index] = tm_hit
                cache[key] = tm_hit
                continue
        pending.append((index, block))

    chunk_size = int(os.getenv("LLM_CHUNK_SIZE", "40"))
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
    backoff = float(os.getenv("LLM_RETRY_BACKOFF", "0.8"))
    context_strategy = os.getenv("LLM_CONTEXT_STRATEGY", "none").lower()
    glossary_path = os.getenv("LLM_GLOSSARY_PATH", "")
    glossary = _load_glossary(glossary_path)

    for chunk in _chunked(pending, chunk_size):
        chunk_blocks = []
        placeholder_maps: list[dict[str, str]] = []
        placeholder_tokens: list[str] = []
        for _, block in chunk:
            prepared = dict(block)
            prepared_text, mapping = _apply_placeholders(
                prepared.get("source_text", ""), preferred_terms
            )
            prepared["source_text"] = prepared_text
            if mapping:
                placeholder_tokens.extend(mapping.keys())
            placeholder_maps.append(mapping)
            chunk_blocks.append(prepared)
        context = _build_context(context_strategy, blocks_list, chunk_blocks)
        attempt = 0
        while True:
            try:
                result = translator.translate(
                    chunk_blocks,
                    target_language,
                    context=context,
                    preferred_terms=preferred_terms,
                    placeholder_tokens=placeholder_tokens,
                )
                result = _coerce_contract(result, chunk_blocks, target_language)
                _validate_contract(result)
                for (original, mapping), translated in zip(
                    zip(chunk, placeholder_maps), result["blocks"]
                ):
                    translated_text = translated.get("translated_text", "")
                    translated_text = _restore_placeholders(translated_text, mapping)
                    if glossary:
                        translated_text = _apply_glossary(translated_text, glossary)
                    translated_texts[original[0]] = translated_text
                    cache[_cache_key(original[1])] = translated_text
                    save_tm(
                        source_lang=os.getenv("SOURCE_LANGUAGE", "auto"),
                        target_lang=target_language,
                        text=_cache_key(original[1]),
                        translated=translated_text,
                    )
                break
            except Exception:
                attempt += 1
                if attempt > max_retries:
                    raise
                time.sleep(backoff * attempt)

    final_texts = [text if text is not None else "" for text in translated_texts]
    return _build_contract(
        blocks=blocks_list,
        translated_texts=final_texts,
        target_language=target_language,
    )
