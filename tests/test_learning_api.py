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

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)


@pytest.fixture
def client():
    return SyncASGIClient()


def test_learning_events_endpoint(client):
    response = client.get("/api/tm/learning-events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)


def test_learning_stats_endpoint(client):
    response = client.get("/api/tm/learning-stats")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)


def test_learning_events_export(client):
    response = client.get("/api/tm/learning-events/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "event_type" in response.text


def test_learning_stats_export(client):
    response = client.get("/api/tm/learning-stats/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "stat_date" in response.text
