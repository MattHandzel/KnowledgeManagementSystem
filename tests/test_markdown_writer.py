import os
from pathlib import Path
from datetime import datetime, timezone
import yaml
import pytest

from markdown_writer import SafeMarkdownWriter


def test_format_capture_frontmatter_rules(tmp_path: Path):
    writer = SafeMarkdownWriter(str(tmp_path))
    ts = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    capture = {
        "timestamp": ts,
        "content": "Hello world",
        "context": "work",
        "tags": ["a", "b"],
        "sources": ["src1"],
        "modalities": ["text"],
    }
    out = writer.format_capture(capture)
    assert out.startswith("---\n")
    assert "\n---\n" in out
    fm_text, body = out.split("\n---\n", 1)
    fm = yaml.safe_load(fm_text.replace("---\n", ""))
    assert fm["timestamp"] == ts.isoformat()
    assert fm["id"] == ts.isoformat()
    assert fm["aliases"] == [ts.isoformat()]
    assert fm["created_date"] == "2025-01-02"
    assert fm["last_edited_date"] == "2025-01-02"
    assert fm.get("importance", None) is None
    assert body.startswith("## Content\n")
    assert "\n\n##" not in out.split("---\n", 2)[2][:3]


def test_atomic_write_and_unique_files(tmp_path: Path):
    writer = SafeMarkdownWriter(str(tmp_path))
    ts = datetime.now(timezone.utc).replace(microsecond=0)
    capture = {"timestamp": ts, "content": "A", "modalities": ["text"]}
    p1 = writer.write_capture(capture)
    assert p1.exists()
    p2 = writer.write_capture(capture)
    assert p2.exists()
    assert p1 != p2


def test_media_relative_path(tmp_path: Path):
    writer = SafeMarkdownWriter(str(tmp_path))
    media_dir = writer.media_dir
    media_dir.mkdir(parents=True, exist_ok=True)
    media_file = media_dir / "x.png"
    media_file.write_bytes(b"abc")
    rel = writer.get_relative_media_path(str(media_file))
    assert not rel.startswith(str(tmp_path))
