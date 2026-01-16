from __future__ import annotations

from typing import Iterable


def _iter_errors(error: BaseException) -> Iterable[BaseException]:
    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def is_connection_refused(error: BaseException) -> bool:
    for item in _iter_errors(error):
        if isinstance(item, ConnectionRefusedError):
            return True
        if isinstance(item, OSError) and item.errno in {111, 10061}:
            return True
        text = str(item)
        if any(
            marker in text
            for marker in (
                "WinError 10061",
                "ECONNREFUSED",
                "Connection refused",
                "Errno 111",
                "Failed to establish a new connection",
                "Connect call failed",
            )
        ):
            return True
    return False


def build_connection_refused_message(provider: str, base_url: str | None) -> str:
    location = base_url or "http://localhost:11434"
    provider_label = provider or "Ollama"
    return f"無法連線到 {provider_label} 服務（{location}），請確認服務已啟動且 Base URL 正確。"
