from backend.services.llm_errors import (
    build_connection_refused_message,
    is_connection_refused,
)

def test_is_connection_refused_with_oserror():
    assert is_connection_refused(ConnectionRefusedError("refused"))


def test_is_connection_refused_with_errno():
    error = OSError(111, "Connection refused")
    assert is_connection_refused(error)


def test_build_connection_refused_message():
    message = build_connection_refused_message("Ollama", "http://localhost:11434")
    assert "Ollama" in message
    assert "http://localhost:11434" in message
