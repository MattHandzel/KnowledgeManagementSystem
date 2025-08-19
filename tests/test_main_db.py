from pathlib import Path
import sqlite3
from datetime import datetime, timezone, timedelta

from server.main_db import MainDatabase


def test_store_and_suggestions(tmp_path: Path):
    db_path = tmp_path / "main.db"
    m = MainDatabase(str(db_path))
    now = datetime.now(timezone.utc).isoformat()
    cap = {
        "capture_id": now,
        "content": "note",
        "context": "coding",
        "tags": ["rust", "python"],
        "sources": ["web"],
        "modalities": ["text"],
        "location": None,
        "metadata": {},
        "created_date": now[:10],
        "last_edited_date": now[:10],
        "file_path": "",
        "media_files": [],
    }
    m.store_capture_data(cap)
    sugg = m.get_suggestions("tag", "py", 10)
    values = [s.value for s in sugg]
    assert "python" in values
    assert m.suggestion_exists("rust", "tag") is True
    recent = m.get_most_recent_values()
    assert "tags" in recent and "sources" in recent and "context" in recent


def test_statistics(tmp_path: Path):
    m = MainDatabase(str(tmp_path / "main.db"))
    for i in range(5):
        ts = datetime.now(timezone.utc).isoformat()
        cap = {
            "capture_id": ts,
            "content": f"c{i}",
            "context": "ctx",
            "tags": ["t1", "t2"],
            "sources": ["s1"],
            "modalities": ["text"],
            "location": None,
            "metadata": {},
            "created_date": ts[:10],
            "last_edited_date": ts[:10],
            "file_path": "",
            "media_files": [],
        }
        m.store_capture_data(cap)
    stats = m.get_capture_statistics()
    assert stats["total_captures"] >= 5
    assert stats["unique_tags"] >= 2
