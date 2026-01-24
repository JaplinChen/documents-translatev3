import os

import time

from backend.api.pptx_naming import generate_semantic_filename_with_ext


def test_generate_semantic_filename_with_ext_respects_extension(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(time, "strftime", lambda *_args, **_kwargs: "20260124")
    filename = generate_semantic_filename_with_ext("sample.xlsx", "translated", "none", ".xlsx")
    assert filename.endswith(".xlsx")


def test_generate_semantic_filename_with_ext_sequences_per_extension(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(time, "strftime", lambda *_args, **_kwargs: "20260124")
    exports = tmp_path / "data" / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    (exports / "sample-translated-none-20260124-001.xlsx").write_bytes(b"1")
    (exports / "sample-translated-none-20260124-001.pdf").write_bytes(b"1")

    filename = generate_semantic_filename_with_ext("sample.xlsx", "translated", "none", ".xlsx")
    assert filename.endswith("-002.xlsx")
