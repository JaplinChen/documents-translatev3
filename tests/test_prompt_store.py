from backend.services import prompt_store


def test_prompt_store_list_and_get(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(prompt_store, "PROMPTS_DIR", tmp_path)
    names = prompt_store.list_prompts()

    assert "translate_json" in names
    content = prompt_store.get_prompt("translate_json")
    assert "{payload}" in content
