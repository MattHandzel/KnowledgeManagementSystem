#!/usr/bin/env python3
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from capture_daemon import CaptureUI, Field


def make_stdscr_mock(width=80, height=24):
    stdscr = MagicMock()
    stdscr.getmaxyx.return_value = (height, width)
    stdscr.clear.return_value = None
    stdscr.refresh.return_value = None
    stdscr.addstr.return_value = None
    stdscr.addch.return_value = None
    stdscr.move.return_value = None
    return stdscr


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
def test_context_tags_alignment(mock_curses):
    mock_curses.A_BOLD = 0x100
    mock_curses.color_pair.side_effect = lambda n=0: 0
    mock_curses.ACS_ULCORNER = 0
    mock_curses.ACS_URCORNER = 0
    mock_curses.ACS_LLCORNER = 0
    mock_curses.ACS_LRCORNER = 0
    mock_curses.ACS_HLINE = 0
    mock_curses.ACS_VLINE = 0
    mock_curses.newwin.side_effect = newwin_factory()

    stdscr = make_stdscr_mock(width=80, height=24)
    ui = CaptureUI({
        'vault': {'path': str(Path.cwd() / "vault"), 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
        'daemon': {'socket_path': '/tmp/capture_daemon.sock'},
        'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True, 'show_help': True},
    })
    ui.initialize_ui(stdscr)
    ui.help_visible = False
    ui.draw_ui()

    calls = [c for c in stdscr.addstr.call_args_list]
    context_call = next((c for c in calls if len(c[0]) >= 3 and c[0][2] == "Context:"), None)
    tags_call = next((c for c in calls if len(c[0]) >= 3 and c[0][2] == "Tags:"), None)
    assert context_call is not None and tags_call is not None

    height, width = stdscr.getmaxyx()
    content_height = max(8, height - 12)
    expected_context_y = 3 + content_height + 1
    expected_tags_y = expected_context_y + 1

    assert context_call[0][0] == expected_context_y
    assert tags_call[0][0] == expected_tags_y


@patch("capture_daemon.curses")
def test_modality_selector_highlight_when_active(mock_curses):
    mock_curses.A_BOLD = 0x100
    mock_curses.color_pair.side_effect = lambda n=0: 0x10 if n == 1 else 0
    mock_curses.ACS_ULCORNER = 0
    mock_curses.ACS_URCORNER = 0
    mock_curses.ACS_LLCORNER = 0
    mock_curses.ACS_LRCORNER = 0
    mock_curses.ACS_HLINE = 0
    mock_curses.ACS_VLINE = 0
    mock_curses.newwin.side_effect = newwin_factory()

    stdscr = make_stdscr_mock(width=80, height=24)
    ui = CaptureUI({
        'vault': {'path': str(Path.cwd() / "vault"), 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
        'daemon': {'socket_path': '/tmp/capture_daemon.sock'},
        'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True, 'show_help': True},
    })
    ui.initialize_ui(stdscr)
    ui.help_visible = False
    ui.set_active_field(Field.MODALITIES)
    ui.modality_index = 0
    ui.draw_ui()

    calls = [c for c in stdscr.addstr.call_args_list]
    mode_calls = [c for c in calls if len(c[0]) >= 3 and isinstance(c[0][2], str) and c[0][2].startswith("Mode:")]
    assert any((len(c[0]) >= 4 and c[0][3] != 0) for c in mode_calls)


@patch("capture_daemon.curses")
def test_save_does_not_stall_on_save(mock_curses, tmp_path, monkeypatch):

    mock_curses.A_BOLD = 0
    mock_curses.color_pair.side_effect = lambda n=0: 0
    mock_curses.ACS_ULCORNER = 0
    mock_curses.ACS_URCORNER = 0
    mock_curses.ACS_LLCORNER = 0
    mock_curses.ACS_LRCORNER = 0
    mock_curses.ACS_HLINE = 0
    mock_curses.ACS_VLINE = 0
    mock_curses.newwin.side_effect = newwin_factory()

    stdscr = make_stdscr_mock()
    seq = [ord('h'), ord('i'), 19]  # type "hi", then Ctrl+S
    def _getch():
        if seq:
            return seq.pop(0)
        return 19
    stdscr.getch.side_effect = _getch

    from capture_daemon import CaptureUI
    config = {
        'vault': {'path': str(tmp_path), 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
        'daemon': {'socket_path': str(tmp_path / 'sock')},
        'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True, 'show_help': True},
    }
    ui = CaptureUI(config)

    def wrapper(func, *args, **kwargs):
        return func(stdscr)
    mock_curses.wrapper.side_effect = lambda f: wrapper(f)

    start = time.monotonic()
    assert ui.run_capture("quick") is True
    duration = time.monotonic() - start
    assert duration < 1.0

    files = list((Path(tmp_path) / "capture" / "raw_capture").glob("*.md"))
    assert files
