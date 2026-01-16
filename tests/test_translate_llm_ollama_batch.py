from backend.services.translate_llm import (
    _build_ollama_batch_prompt,
    _parse_ollama_batch_response,
)


def test_build_ollama_batch_prompt_includes_blocks() -> None:
    blocks = [{"source_text": "Hello"}, {"source_text": "World"}]
    prompt = _build_ollama_batch_prompt(blocks, "zh-TW")
    assert "目標語言：Traditional Chinese (zh-TW)" in prompt
    assert "目標語言代碼：zh-TW" in prompt
    assert "<<<BLOCK:0>>>" in prompt
    assert "Hello" in prompt
    assert "<<<BLOCK:1>>>" in prompt
    assert "World" in prompt


def test_parse_ollama_batch_response_success() -> None:
    response = (
        "<<<BLOCK:0>>>\n你好\n<<<END>>>\n\n"
        "<<<BLOCK:1>>>\n世界\n<<<END>>>\n"
    )
    parsed = _parse_ollama_batch_response(response, 2)
    assert parsed == ["你好", "世界"]


def test_parse_ollama_batch_response_missing_block() -> None:
    response = "<<<BLOCK:0>>>\n你好\n<<<END>>>\n"
    parsed = _parse_ollama_batch_response(response, 2)
    assert parsed is None
