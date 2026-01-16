from backend.services import translation_memory


def test_clear_tm_removes_all_rows(tmp_path) -> None:
    translation_memory.DB_PATH = tmp_path / "tm.db"
    translation_memory.seed_tm(
        [
            ("vi", "zh-TW", "hello", "哈囉"),
            ("en", "zh-TW", "world", "世界"),
        ]
    )

    assert len(translation_memory.get_tm()) == 2
    deleted = translation_memory.clear_tm()

    assert deleted == 2
    assert translation_memory.get_tm() == []
