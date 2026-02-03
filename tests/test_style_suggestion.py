import anyio
import httpx
import pytest
from httpx import ASGITransport

from backend.main import app

class SyncASGIClient:
    def request(self, method: str, url: str, **kwargs):
        async def _run():
            transport = ASGITransport(app=app, raise_app_exceptions=True)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                return await client.request(method, url, **kwargs)

        return anyio.run(_run)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)


@pytest.fixture
def client():
    return SyncASGIClient()

def test_style_suggestion_endpoint(client):
    # 1. Prepare sample blocks
    sample_blocks = [
        {"source_text": "Welcome to our high-tech presentation", "block_type": "textbox"},
        {"source_text": "Artificial Intelligence is the future", "block_type": "textbox"},
        {"source_text": "Quarterly financial report 2024", "block_type": "textbox"}
    ]

    # 2. Call endpoint
    response = client.post("/api/style/suggest", json={"blocks": sample_blocks})

    assert response.status_code == 200
    data = response.json()

    # 3. Verify schema
    assert "theme_name" in data
    assert "primary_color" in data
    assert "secondary_color" in data
    assert "accent_color" in data
    assert "font_recommendation" in data
    assert "rationale" in data

    # Colors should be hex strings
    assert data["primary_color"].startswith("#")
    assert len(data["primary_color"]) == 7
