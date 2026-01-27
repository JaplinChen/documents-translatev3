from __future__ import annotations

import json
from urllib.request import Request, urlopen

def list_openai_models(api_key: str, base_url: str) -> list[str]:
    request = Request(
        f"{base_url.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    models = [item.get("id") for item in data.get("data", [])]
    return sorted([model for model in models if model])


def list_gemini_models(api_key: str, base_url: str) -> list[str]:
    request = Request(
        f"{base_url.rstrip('/')}/models?key={api_key}",
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    models = []
    for item in data.get("models", []):
        name = item.get("name", "")
        supported = item.get("supportedGenerationMethods", [])
        if "generateContent" in supported and name.startswith("models/"):
            models.append(name.replace("models/", ""))
    return sorted(models)


def list_ollama_models(base_url: str) -> list[str]:
    request = Request(
        f"{base_url.rstrip('/')}/api/tags",
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    models = [item.get("name") for item in data.get("models", [])]
    return sorted([model for model in models if model])
