import json
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.tools.logging_middleware import StructuredLoggingMiddleware

app = FastAPI()
app.add_middleware(StructuredLoggingMiddleware)


@app.get("/test-log")
async def test_endpoint():
    return {"status": "ok"}


@app.get("/test-error")
async def error_endpoint():
    raise ValueError("Test Error")


client = TestClient(app)


def test_logging_middleware_success(caplog):
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


def test_logging_middleware_error(caplog):
    caplog.set_level(logging.ERROR)
    with pytest.raises(ValueError):
        client.get("/test-error")

    log_messages = [
        json.loads(record.message)
        for record in caplog.records
        if "event" in record.message
    ]
    assert any(m["event"] == "request_failed" for m in log_messages)
