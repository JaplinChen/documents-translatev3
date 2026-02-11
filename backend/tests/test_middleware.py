import json
import logging

import anyio
import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from backend.tools.logging_middleware import StructuredLoggingMiddleware

app = FastAPI()
app.add_middleware(StructuredLoggingMiddleware)


@app.get("/test-log")
async def log_endpoint():
    return {"status": "ok"}


@app.get("/test-error")
async def error_endpoint():
    raise ValueError("Test Error")


class SyncASGIClient:
    def __init__(self, app: FastAPI):
        self._app = app

    def request(self, method: str, url: str, **kwargs):
        async def _run():
            transport = ASGITransport(app=self._app, raise_app_exceptions=True)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                return await client.request(method, url, **kwargs)

        return anyio.run(_run)

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)


@pytest.fixture
def client():
    return SyncASGIClient(app)


def test_logging_middleware_success(caplog, client):
    caplog.set_level(logging.INFO)
    response = client.get("/test-log")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

    # Check if JSON logs are present
    log_messages = [
        json.loads(record.message)
        for record in caplog.records
        if "event" in record.message
    ]
    assert any(m["event"] == "request_received" for m in log_messages)
    assert any(m["event"] == "request_finished" for m in log_messages)


def test_logging_middleware_error(caplog, client):
    caplog.set_level(logging.ERROR)
    with pytest.raises(ValueError):
        client.get("/test-error")

    log_messages = [
        json.loads(record.message)
        for record in caplog.records
        if "event" in record.message
    ]
    assert any(m["event"] == "request_failed" for m in log_messages)
