#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from capture_daemon import CaptureUI


@pytest.fixture
def tmp_vault(tmp_path):
    vault_root = tmp_path / "vault"
    (vault_root / "capture" / "raw_capture" / "media").mkdir(parents=True, exist_ok=True)
    return str(vault_root)


def make_stdscr_mock(width=100, height=30, key_sequence=None):
    if key_sequence is None:
        key_sequence = []

    stdscr = MagicMock()
    stdscr.getmaxyx.return_value = (height, width)
    stdscr.clear.return_value = None
    stdscr.refresh.return_value = None
    stdscr.addstr.return_value = None
    stdscr.addch.return_value = None
    stdscr.move.return_value = None

    seq = list(key_sequence)

    def _getch():
        if seq:
            return seq.pop(0)
        return 19

    stdscr.getch.side_effect = _getch
    return stdscr


def run_ui_with_mock_wrapper(ui: CaptureUI, stdscr: MagicMock):
    def _wrapper(func, *args, **kwargs):
        return func(stdscr)
    return _wrapper


def newwin_factory():
    def _newwin(nlines, ncols, begin_y, begin_x):
        win = MagicMock()
        win.getmaxyx.return_value = (nlines, ncols)
        win.clear.return_value = None
        win.refresh.return_value = None
        win.addstr.return_value = None
        win.addch.return_value = None
        win.move.return_value = None
        return win
    return _newwin


@patch("capture_daemon.curses")
@patch.dict(os.environ, {"TERM": "xterm-256color"})
@patch("capture_daemon.sys.stdin", autospec=True)
def test_quick_mode_run_saves_file_and_no_none_stdscr(mock_stdin, mock_curses, tmp_vault, tmp_path):
    mock_stdin.isatty.return_value = True

    config = {
        'vault': {'path': tmp_vault, 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
        'daemon': {'socket_path': str(tmp_path / 'sock')},
        'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True, 'show_help': True},
    }
    ui = CaptureUI(config)

    mock_curses.A_BOLD = 0
    mock_curses.color_pair.side_effect = lambda n=0: 0
    mock_curses.ACS_ULCORNER = 0
    mock_curses.ACS_URCORNER = 0
    mock_curses.ACS_LLCORNER = 0
    mock_curses.ACS_LRCORNER = 0
    mock_curses.ACS_HLINE = 0
    mock_curses.ACS_VLINE = 0
    mock_curses.newwin.side_effect = newwin_factory()

    stdscr = make_stdscr_mock(key_sequence=[ord('x'), ord('a'), 19])

    mock_curses.wrapper.side_effect = run_ui_with_mock_wrapper(ui, stdscr)

    with patch("subprocess.run"):
        result = ui.run_capture("quick")
    assert result is True

    capture_dir = Path(tmp_vault).expanduser() / 'capture' / 'raw_capture'
    files = list(capture_dir.glob("*.md"))
    assert len(files) >= 1


@patch("capture_daemon.curses")
@patch.dict(os.environ, {"TERM": "xterm-256color"})
@patch("capture_daemon.sys.stdin", autospec=True)
def test_help_toggle_then_typing_keeps_content_visible_path(mock_stdin, mock_curses, tmp_vault, tmp_path):
    mock_stdin.isatty.return_value = True

    config = {
        'vault': {'path': tmp_vault, 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
        'daemon': {'socket_path': str(tmp_path / 'sock')},
        'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True, 'show_help': True},
    }
    ui = CaptureUI(config)

    mock_curses.A_BOLD = 0
    mock_curses.color_pair.side_effect = lambda n=0: 0
    mock_curses.ACS_ULCORNER = 0
    mock_curses.ACS_URCORNER = 0
    mock_curses.ACS_LLCORNER = 0
    mock_curses.ACS_LRCORNER = 0
    mock_curses.ACS_HLINE = 0
    mock_curses.ACS_VLINE = 0
    mock_curses.newwin.side_effect = newwin_factory()

    drew_content = {'count': 0}
    orig_draw_content = ui.draw_content

    def wrapped_draw_content():
        drew_content['count'] += 1
        return orig_draw_content()

    ui.draw_content = wrapped_draw_content

    stdscr = make_stdscr_mock(key_sequence=[ord('x'), ord('b'), 19])

    mock_curses.wrapper.side_effect = run_ui_with_mock_wrapper(ui, stdscr)

    with patch("subprocess.run"):
        result = ui.run_capture("quick")
    assert result is True
    assert drew_content['count'] >= 1

@patch("capture_daemon.curses")
@patch.dict(os.environ, {"TERM": "xterm-256color"})
@patch("capture_daemon.sys.stdin", autospec=True)
def test_quick_mode_save_with_none_stdscr_does_not_crash(mock_stdin, mock_curses, tmp_vault, tmp_path):
    mock_stdin.isatty.return_value = True

    config = {
        'vault': {'path': tmp_vault, 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
        'daemon': {'socket_path': str(tmp_path / 'sock')},
        'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True, 'show_help': True},
    }
    ui = CaptureUI(config)

    mock_curses.A_BOLD = 0
    mock_curses.color_pair.side_effect = lambda n=0: 0
    mock_curses.ACS_ULCORNER = 0
    mock_curses.ACS_URCORNER = 0
    mock_curses.ACS_LLCORNER = 0
    mock_curses.ACS_LRCORNER = 0
    mock_curses.ACS_HLINE = 0
    mock_curses.ACS_VLINE = 0
    mock_curses.newwin.side_effect = newwin_factory()

    stdscr = make_stdscr_mock(key_sequence=[ord('q'), ord('u'), ord('i'), ord('c'), ord('k'), 19])
    mock_curses.wrapper.side_effect = run_ui_with_mock_wrapper(ui, stdscr)

    orig_save = ui.save_capture
    def wrapped_save():
        saved_stdscr = ui.stdscr
        try:
            ui.stdscr = None
            return orig_save()
        finally:
            ui.stdscr = saved_stdscr
    ui.save_capture = wrapped_save

    with patch("subprocess.run"):
        result = ui.run_capture("quick")
    assert result is True

    capture_dir = Path(tmp_vault).expanduser() / 'capture' / 'raw_capture'
    files = list(capture_dir.glob("*.md"))
    assert len(files) >= 1
