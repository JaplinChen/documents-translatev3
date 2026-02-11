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

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)


@pytest.fixture
def client():
    return SyncASGIClient()


def test_layouts_list_contract(client):
    response = client.get(
        "/api/layouts",
        params={"file_type": "xlsx", "mode": "bilingual"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "layouts" in body
    assert isinstance(body["layouts"], list)
    assert len(body["layouts"]) >= 1
    item = body["layouts"][0]
    for key in [
        "id",
        "name",
        "file_type",
        "modes",
        "apply_value",
        "enabled",
        "is_custom",
        "params_schema",
    ]:
        assert key in item


def test_layouts_import_preview_contract(client):
    payload = {
        "layouts": [
            {
                "id": "custom_contract_preview_1",
                "name": "Contract Check",
                "file_type": "pdf",
                "modes": ["bilingual"],
                "apply_value": "inline",
                "enabled": True,
                "params_schema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                },
            }
        ],
        "mode": "merge",
        "file_type": "pdf",
    }
    response = client.post("/api/layouts/custom/import-preview", json=payload)
    assert response.status_code == 200
    body = response.json()
    for key in [
        "status",
        "received",
        "valid",
        "skipped",
        "created",
        "updated",
        "unchanged",
        "replace_scope_existing",
        "details",
    ]:
        assert key in body
    assert body["status"] == "success"
    assert isinstance(body["details"], list)
    if body["details"]:
        d = body["details"][0]
        for k in ["file_type", "id", "key", "action", "name", "changed_fields"]:
            assert k in d

