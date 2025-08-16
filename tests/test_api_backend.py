import io
from pathlib import Path
from datetime import datetime, timezone
import yaml
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # type: ignore

import server.app as appmod


def test_api_config_reads_config(monkeypatch, tmp_path):
    cfg = {
        "vault": {
            "path": str(tmp_path),
            "capture_dir": "capture/raw_capture",
            "media_dir": "capture/raw_capture/media",
        },
        "ui": {"clipboard_poll_ms": 150},
        "capture": {"auto_detect_modalities": True},
    }

    monkeypatch.setattr(appmod, "load_config", lambda: cfg)
    client = TestClient(appmod.app)
    r = client.get("/api/config")
    assert r.status_code == 200
    data = r.json()
    assert data["vault"]["path"] == str(tmp_path)
    assert data["vault"]["capture_dir"] == "capture/raw_capture"
    assert data["vault"]["media_dir"] == "capture/raw_capture/media"
    assert data["ui"]["clipboard_poll_ms"] == 150


def test_api_capture_writes_markdown_and_media(monkeypatch, tmp_path):
    cfg = {
        "vault": {
            "path": str(tmp_path),
            "capture_dir": "capture/raw_capture",
            "media_dir": "capture/raw_capture/media",
        },
        "ui": {"clipboard_poll_ms": 200},
        "capture": {},
    }
    monkeypatch.setattr(appmod, "load_config", lambda: cfg)
    client = TestClient(appmod.app)

    files = [
        ("media", ("shot.png", b"fakepng", "image/png")),
        ("media", ("doc.txt", b"hello", "text/plain")),
    ]
    data = {
        "content": "Web app saved content",
        "context": "activity: testing",
        "tags": "web,api",
        "sources": "website: example.com, note: abc",
        "modalities": "text,files",
        "created_date": "2025-08-16",
        "last_edited_date": "2025-08-16",
    }
    r = client.post("/api/capture", data=data, files=files)
    assert r.status_code == 200
    saved_to = r.json()["saved_to"]
    p = Path(saved_to)
    assert p.exists()
    content = p.read_text()

    parts = content.split("---", 2)
    assert len(parts) >= 3
    frontmatter = yaml.safe_load(parts[1])

    ts = frontmatter["timestamp"]
    parsed = datetime.fromisoformat(ts)
    assert parsed.tzinfo is not None
    assert parsed.tzinfo.utcoffset(parsed).total_seconds() == 0
    assert parsed.microsecond == 0

    assert frontmatter["id"] == frontmatter["capture_id"]
    assert frontmatter["aliases"] == [frontmatter["capture_id"]]
    assert frontmatter.get("importance") is None
    assert frontmatter["created_date"] == "2025-08-16"
    assert frontmatter["last_edited_date"] == "2025-08-16"
    assert frontmatter["sources"] == ["website: example.com", "note: abc"]
    assert "\n---\n##" in content

    media_dir = Path(cfg["vault"]["path"]) / cfg["vault"]["media_dir"]
    assert (media_dir / "shot.png").exists()
    assert (media_dir / "doc.txt").exists()
