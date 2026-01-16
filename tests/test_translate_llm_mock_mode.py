from backend.services.translate_llm import translate_blocks


def test_translate_blocks_mock_mode_ignores_provider(monkeypatch):
    monkeypatch.setenv("TRANSLATE_LLM_MODE", "mock")
    blocks = [
        {
            "slide_index": 0,
            "shape_id": 1,
            "block_type": "textbox",
            "source_text": "Test text",
            "translated_text": "",
            "client_id": "block-1",
        }
    ]

    result = translate_blocks(
        blocks,
        target_language="zh-TW",
        provider="ollama",
        base_url="http://localhost:12345",
        model="llama3.1",
    )

    assert result["blocks"][0]["translated_text"] == "Test text"
