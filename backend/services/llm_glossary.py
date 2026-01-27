from __future__ import annotations

import csv

def load_glossary(path: str | None) -> list[tuple[str, str]]:
    if not path:
        return []
    entries: list[tuple[str, str]] = []
    with open(path, encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            source = row[0].strip()
            target = row[1].strip()
            if source:
                entries.append((source, target))
    return entries


def apply_glossary(text: str, glossary: list[tuple[str, str]]) -> str:
    updated = text
    for source, target in glossary:
        updated = updated.replace(source, target)
    return updated
