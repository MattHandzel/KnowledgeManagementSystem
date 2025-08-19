import os
import sys
from types import SimpleNamespace
from pathlib import Path
from fastapi.testclient import TestClient

sys.modules.setdefault(
    "sounddevice",
    SimpleNamespace(InputStream=None, query_devices=lambda *a, **k: {}),
)

from server.app import app, normalize_config


def test_config_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("KMS_DB_PATH", str(tmp_path / "main.db"))
    monkeypatch.setenv("KMS_VAULT_PATH", str(tmp_path))
    c = TestClient(app)
    r = c.get("/api/config")
    assert r.status_code == 200
    data = r.json()
    assert "vault" in data and "database" in data


def test_capture_and_suggestions(tmp_path, monkeypatch):
    monkeypatch.setenv("KMS_DB_PATH", str(tmp_path / "main.db"))
    monkeypatch.setenv("KMS_VAULT_PATH", str(tmp_path))
    c = TestClient(app)

    r = c.post(
        "/api/capture",
        data={
            "content": "hello",
            "context": "work",
            "tags": "a,b",
            "sources": "s1",
            "modalities": "text",
        },
    )
    assert r.status_code == 200
    saved = r.json()
    assert "saved_to" in saved

    r2 = c.get("/api/suggestions/tag", params={"query": "a", "limit": 5})
    assert r2.status_code == 200
    assert "suggestions" in r2.json()


def test_clipboard_endpoint():
    c = TestClient(app)
    r = c.get("/api/clipboard")
    assert r.status_code == 200
    assert "content" in r.json()


def test_screenshot_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("KMS_VAULT_PATH", str(tmp_path))
    c = TestClient(app)
    r = c.post("/api/screenshot")
    assert r.status_code == 200
    data = r.json()
    assert "success" in data
