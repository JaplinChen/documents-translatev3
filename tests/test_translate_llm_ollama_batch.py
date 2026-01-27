from backend.services.translate_prompt import (
    build_ollama_batch_prompt,
    parse_ollama_batch_response,
)

def test_build_ollama_batch_prompt_includes_blocks() -> None:
    blocks = [{"source_text": "Hello"}, {"source_text": "World"}]
    prompt = build_ollama_batch_prompt(blocks, "zh-TW")
    assert "zh-TW" in prompt or "Traditional Chinese" in prompt
    assert "<<<BLOCK:0>>>" in prompt
    assert "Hello" in prompt
    assert "<<<BLOCK:1>>>" in prompt
    assert "World" in prompt


def test_parse_ollama_batch_response_success() -> None:
    response = "<<<BLOCK:0>>>\n你好\n<<<END>>>\n\n<<<BLOCK:1>>>\n世界\n<<<END>>>\n"
    parsed = parse_ollama_batch_response(response, 2)
    assert parsed == ["你好", "世界"]


def test_parse_ollama_batch_response_missing_block() -> None:
    response = "<<<BLOCK:0>>>\n你好\n<<<END>>>\n"
    parsed = parse_ollama_batch_response(response, 2)
    assert parsed is None
