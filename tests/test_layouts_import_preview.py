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


def _cleanup_file_type(client: SyncASGIClient, file_type: str) -> None:
    client.post(
        "/api/layouts/custom/import",
        json={
            "layouts": [],
            "mode": "replace",
            "file_type": file_type,
        },
    )


def test_layout_import_preview_includes_changed_fields(client):
    file_type = "docx"
    _cleanup_file_type(client, file_type)

    base = {
        "id": "custom_docx_preview_1",
        "name": "Base Name",
        "file_type": file_type,
        "modes": ["bilingual"],
        "apply_value": "inline",
        "enabled": True,
        "params_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        },
    }
    create_resp = client.post("/api/layouts/custom", json=base)
    assert create_resp.status_code == 200

    incoming = dict(base)
    incoming["name"] = "Incoming Name"
    incoming["enabled"] = False

    preview_resp = client.post(
        "/api/layouts/custom/import-preview",
        json={
            "layouts": [incoming],
            "mode": "merge",
            "file_type": file_type,
        },
    )
    assert preview_resp.status_code == 200
    body = preview_resp.json()
    assert body["updated"] == 1
    assert len(body["details"]) == 1
    detail = body["details"][0]
    assert detail["action"] == "update"
    assert "name" in detail["changed_fields"]
    assert "enabled" in detail["changed_fields"]

    _cleanup_file_type(client, file_type)


def test_layout_import_decision_keep_existing(client):
    file_type = "xlsx"
    _cleanup_file_type(client, file_type)

    base = {
        "id": "custom_xlsx_decision_1",
        "name": "Original Name",
        "file_type": file_type,
        "modes": ["bilingual"],
        "apply_value": "inline",
        "enabled": True,
        "params_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        },
    }
    create_resp = client.post("/api/layouts/custom", json=base)
    assert create_resp.status_code == 200

    incoming = dict(base)
    incoming["name"] = "Incoming Name"

    preview_resp = client.post(
        "/api/layouts/custom/import-preview",
        json={
            "layouts": [incoming],
            "mode": "merge",
            "file_type": file_type,
        },
    )
    assert preview_resp.status_code == 200
    detail = preview_resp.json()["details"][0]
    decision_key = detail["key"]

    import_resp = client.post(
        "/api/layouts/custom/import",
        json={
            "layouts": [incoming],
            "mode": "merge",
            "file_type": file_type,
            "decisions": {
                decision_key: "keep_existing",
            },
        },
    )
    assert import_resp.status_code == 200
    assert import_resp.json().get("skipped_by_decision") == 1

    export_resp = client.get("/api/layouts/custom/export", params={"file_type": file_type})
    assert export_resp.status_code == 200
    layouts = export_resp.json().get("layouts", [])
    assert len(layouts) == 1
    assert layouts[0]["name"] == "Original Name"

    _cleanup_file_type(client, file_type)

