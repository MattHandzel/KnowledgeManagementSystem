from pathlib import Path
import json


def test_electron_package_has_entrypoints():
    pkg = Path("electron/package.json")
    assert pkg.exists()
    data = json.loads(pkg.read_text())
    assert "main" in data or "scripts" in data
