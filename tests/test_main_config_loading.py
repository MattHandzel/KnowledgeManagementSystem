#!/usr/bin/env python3
import os
import sys
import importlib
from pathlib import Path
from unittest.mock import patch

import pytest


@patch.dict(os.environ, {"TERM": "xterm-256color"})
@patch("capture_daemon.sys.stdin", autospec=True)
def test_main_uses_config_yaml_for_vault_path_without_override(mock_stdin, tmp_path, capsys):
    mock_stdin.isatty.return_value = True

    vault = tmp_path / "vaultA"
    (vault / "capture" / "raw_capture" / "media").mkdir(parents=True, exist_ok=True)

    cfg = {
        'vault': {'path': str(vault), 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
        'daemon': {'socket_path': str(tmp_path / 'sock')},
        'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True, 'show_help': True},
    }
    cfg_path = tmp_path / "config.yaml"
    import yaml as _yaml
    cfg_path.write_text(_yaml.dump(cfg))

    import capture_daemon
    def fake_run_capture(self, mode):
        data = {
            'timestamp': __import__('datetime').datetime.now(),
            'content': 'test',
            'context': {},
            'tags': [],
            'modalities': ['text'],
        }
        result = self.writer.write_capture(data)
        self.last_saved_file = str(result)
        return True

    with patch.object(sys, "argv", [str(Path("capture_daemon.py")), "--mode", "quick", "--config", str(cfg_path)]):
        importlib.reload(capture_daemon)
        with patch.object(capture_daemon.CaptureUI, "run_capture", fake_run_capture):
            with pytest.raises(SystemExit):
                capture_daemon.main()

    out = capsys.readouterr().out
    assert "Saved to:" in out
    files = list((vault / "capture" / "raw_capture").glob("*.md"))
    assert len(files) >= 1


@patch.dict(os.environ, {"TERM": "xterm-256color"})
@patch("capture_daemon.sys.stdin", autospec=True)
def test_main_respects_vault_path_override(mock_stdin, tmp_path, capsys):
    mock_stdin.isatty.return_value = True

    vault_default = tmp_path / "vaultDefault"
    (vault_default / "capture" / "raw_capture" / "media").mkdir(parents=True, exist_ok=True)

    vault_override = tmp_path / "vaultOverride"
    (vault_override / "capture" / "raw_capture" / "media").mkdir(parents=True, exist_ok=True)

    cfg = {
        'vault': {'path': str(vault_default), 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
        'daemon': {'socket_path': str(tmp_path / 'sock')},
        'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True, 'show_help': True},
    }
    cfg_path = tmp_path / "config.yaml"
    import yaml as _yaml
    cfg_path.write_text(_yaml.dump(cfg))

    import capture_daemon
    def fake_run_capture(self, mode):
        data = {
            'timestamp': __import__('datetime').datetime.now(),
            'content': 'override',
            'context': {},
            'tags': [],
            'modalities': ['text'],
        }
        result = self.writer.write_capture(data)
        self.last_saved_file = str(result)
        return True

    with patch.object(sys, "argv", [str(Path("capture_daemon.py")), "--mode", "quick", "--config", str(cfg_path), "--vault-path", str(vault_override)]):
        importlib.reload(capture_daemon)
        with patch.object(capture_daemon.CaptureUI, "run_capture", fake_run_capture):
            with pytest.raises(SystemExit):
                capture_daemon.main()

    out = capsys.readouterr().out
    assert "Saved to:" in out
    files_default = list((vault_default / "capture" / "raw_capture").glob("*.md"))
    files_override = list((vault_override / "capture" / "raw_capture").glob("*.md"))
    assert len(files_default) == 0
    assert len(files_override) >= 1
