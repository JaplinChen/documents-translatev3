from backend.config import settings
from backend.services.llm_clients import build_ollama_options

def test_build_ollama_options_empty_by_default(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ollama_num_gpu", None)
    monkeypatch.setattr(settings, "ollama_num_gpu_layers", None)
    monkeypatch.setattr(settings, "ollama_num_ctx", None)
    monkeypatch.setattr(settings, "ollama_num_thread", None)
    monkeypatch.setattr(settings, "ollama_force_gpu", False)
    assert build_ollama_options() == {}


def test_build_ollama_options_force_gpu_sets_default(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ollama_num_gpu", None)
    monkeypatch.setattr(settings, "ollama_num_gpu_layers", None)
    monkeypatch.setattr(settings, "ollama_force_gpu", True)
    assert build_ollama_options() == {"num_gpu": 1}


def test_build_ollama_options_respects_explicit_values(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ollama_num_gpu", 2)
    monkeypatch.setattr(settings, "ollama_num_ctx", 4096)
    monkeypatch.setattr(settings, "ollama_num_thread", 8)
    monkeypatch.setattr(settings, "ollama_force_gpu", True)
    assert build_ollama_options() == {
        "num_gpu": 2,
        "num_ctx": 4096,
        "num_thread": 8,
    }
