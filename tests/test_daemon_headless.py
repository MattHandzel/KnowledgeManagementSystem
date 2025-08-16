#!/usr/bin/env python3
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from capture_daemon import CaptureDaemon

@pytest.fixture
def base_config(tmp_path):
    return {
        'vault': {'path': str(tmp_path), 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
        'daemon': {'socket_path': '/tmp/capture_daemon.sock', 'auto_start': False, 'hot_reload': False},
        'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True, 'show_help': True},
    }

@patch.dict(os.environ, {'TERM': 'dumb'})
@patch('capture_daemon.subprocess.Popen')
@patch('capture_daemon.sys.stdin', autospec=True)
def test_show_capture_ui_spawns_kitty_when_headless(mock_stdin, mock_popen, base_config, monkeypatch):
    mock_stdin.isatty.return_value = False
    d = CaptureDaemon(base_config)
    d.show_capture_ui('quick')
    assert mock_popen.called
    args, kwargs = mock_popen.call_args
    assert 'kitty' in args[0]
    assert '--mode' in args[0]
    assert 'quick' in args[0]

class DummySocket:
    def __init__(self):
        self.sent = []
        self.closed = False
    def send(self, data: bytes):
        raise BrokenPipeError("client disconnected")
    def recv(self, n):
        return b'status'
    def close(self):
        self.closed = True

def test_handle_client_broken_pipe_is_handled(base_config):
    d = CaptureDaemon(base_config)
    sock = DummySocket()
    d.handle_client(sock)
    assert sock.closed is True
