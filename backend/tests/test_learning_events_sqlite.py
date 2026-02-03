from __future__ import annotations

from pathlib import Path

import pytest

from backend.services.translation_memory_sqlite import db as sqlite_db
from backend.services.translation_memory_sqlite import learning as learning_sqlite


def _setup_temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    temp_db = tmp_path / "translation_memory.db"
    monkeypatch.setattr(sqlite_db, "DB_PATH", temp_db)
    monkeypatch.setattr(sqlite_db, "_DB_INITIALIZED", False)
    monkeypatch.setattr(learning_sqlite, "DB_PATH", temp_db)
    sqlite_db._ensure_db()
    return learning_sqlite


def test_record_learning_events_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    learning = _setup_temp_db(tmp_path, monkeypatch)

    learning._record_learning_event(
        "lookup_hit_tm",
        source_text="Hello",
        target_text="你好",
        source_lang="en",
        target_lang="zh",
        scope_type="project",
        scope_id="default",
    )
    learning._record_learning_event(
        "lookup_miss",
        source_text="World",
        target_text=None,
        source_lang="en",
        target_lang="zh",
        scope_type="project",
        scope_id="default",
    )
    learning._record_learning_event(
        "overwrite",
        source_text="Cache",
        target_text="快取",
        source_lang="en",
        target_lang="zh",
        entity_type="tm",
        entity_id=1,
        scope_type="project",
        scope_id="default",
    )

    items, total = learning.list_learning_events(
        limit=10,
        offset=0,
        scope_type="project",
        scope_id="default",
        sort_by="id",
        sort_dir="asc",
    )

    assert total == 3
    assert [item["event_type"] for item in items] == [
        "lookup_hit_tm",
        "lookup_miss",
        "overwrite",
    ]

    hit_items, hit_total = learning.list_learning_events(
        event_type="lookup_hit_tm",
        scope_type="project",
        scope_id="default",
    )
    assert hit_total == 1
    assert hit_items[0]["source_text"] == "Hello"

    miss_items, miss_total = learning.list_learning_events(
        event_type="lookup_miss",
        scope_type="project",
        scope_id="default",
    )
    assert miss_total == 1
    assert miss_items[0]["source_text"] == "World"

    overwrite_items, overwrite_total = learning.list_learning_events(
        event_type="overwrite",
        scope_type="project",
        scope_id="default",
    )
    assert overwrite_total == 1
    assert overwrite_items[0]["entity_type"] == "tm"
    assert overwrite_items[0]["entity_id"] == 1
