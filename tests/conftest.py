import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = PROJECT_ROOT / "server"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

@pytest.fixture(autouse=True)
def isolate_env_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("KMS_DB_PATH", str(tmp_path / "main.db"))
    monkeypatch.setenv("KMS_VAULT_PATH", str(tmp_path))
    monkeypatch.setenv("KMS_ROOT", str(PROJECT_ROOT))
    yield


def pytest_collection_modifyitems(items):
    pass
