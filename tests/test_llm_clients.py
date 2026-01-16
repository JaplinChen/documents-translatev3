import os

from backend.services.llm_clients import build_ollama_options


def test_build_ollama_options_empty_by_default() -> None:
    for key in (
        "OLLAMA_NUM_GPU",
        "OLLAMA_NUM_GPU_LAYERS",
        "OLLAMA_NUM_CTX",
        "OLLAMA_NUM_THREAD",
        "OLLAMA_FORCE_GPU",
    ):
        os.environ.pop(key, None)
    assert build_ollama_options() == {}


def test_build_ollama_options_force_gpu_sets_default() -> None:
    for key in (
        "OLLAMA_NUM_GPU",
        "OLLAMA_NUM_GPU_LAYERS",
        "OLLAMA_NUM_CTX",
        "OLLAMA_NUM_THREAD",
    ):
        os.environ.pop(key, None)
    os.environ["OLLAMA_FORCE_GPU"] = "1"
    assert build_ollama_options() == {"num_gpu": 1}


def test_build_ollama_options_respects_explicit_values() -> None:
    os.environ["OLLAMA_NUM_GPU"] = "2"
    os.environ["OLLAMA_NUM_CTX"] = "4096"
    os.environ["OLLAMA_NUM_THREAD"] = "8"
    os.environ["OLLAMA_FORCE_GPU"] = "1"
    assert build_ollama_options() == {
        "num_gpu": 2,
        "num_ctx": 4096,
        "num_thread": 8,
    }
