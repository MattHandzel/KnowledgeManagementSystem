#!/usr/bin/env python3
"""
Terminal-based knowledge capture daemon with ncurses UI.
Provides instant popup capture interface with semantic keybindings.
"""

import curses
import socket
import json
import threading
import signal
import sys
import os
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from markdown_writer import SafeMarkdownWriter
from keybindings import SemanticKeybindings, Field, HelpDisplay, UIMode
from geolocation import get_device_location


class CaptureUI:
    """ncurses-based capture interface with semantic keybindings."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.writer = SafeMarkdownWriter(config['vault']['path'])
        
        self.content = ""
        self.context = ""
        self.tags = ""
        self.sources = ""
        self.active_modalities = {"text"}
        self.available_modalities = ["text", "clipboard", "screenshot", "audio", "files"]
        
        self.ui_mode = UIMode.INSERT
        self.idea_files = []
        self.selected_idea_index = 0
        self.current_idea_file = None
        
        self.content_cursor = 0
        self.content_scroll = 0
        self.context_cursor = 0
        self.tags_cursor = 0
        self.sources_cursor = 0
        self.modality_index = 0
        
        self.stdscr = None
        self.content_win = None
        self.context_win = None
        self.tags_win = None
        self.sources_win = None
        self.modalities_win = None
        self.help_win = None
        self.idea_list_win = None
        self.active_field = Field.CONTENT
        self.show_help = False
        
        self.keybindings = None
        
        self.capture_data = {}
    
    def initialize_ui(self, stdscr):
        """Initialize the ncurses interface."""
        self.stdscr = stdscr
        curses.curs_set(1)  # Show cursor
        
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Active field
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Headers
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)     # Error
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Help
        
        self.create_windows()
        
        self.keybindings = SemanticKeybindings(self)
        
        self.draw_ui()
    
    def create_windows(self):
        """Create and position UI windows."""
        height, width = self.stdscr.getmaxyx()
        
        content_height = max(8, height - 12)
        self.content_win = curses.newwin(content_height, width - 4, 3, 2)
        
        context_y = 3 + content_height + 1
        self.context_win = curses.newwin(1, width - 20, context_y, 10)
        
        tags_y = context_y + 1
        self.tags_win = curses.newwin(1, width - 20, tags_y, 10)
        
        modalities_y = tags_y + 2
        self.modalities_win = curses.newwin(1, width - 4, modalities_y, 2)
        
        self.help_win = curses.newwin(height - 2, width - 4, 1, 2)
    
    def draw_ui(self):
        """Draw the complete UI."""
        if self.show_help:
            self.draw_help()
            return
        
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        title = "Terminal Capture Daemon"
        self.stdscr.addstr(0, (width - len(title)) // 2, title, 
                          curses.color_pair(2) | curses.A_BOLD)
        
        modalities_text = " ".join([
            f"[{mod.upper()}]" if mod in self.active_modalities else f" {mod.upper()} "
            for mod in self.available_modalities
        ])
        self.stdscr.addstr(1, 2, f"Mode: {modalities_text}")
        
        content_active = self.active_field == Field.CONTENT
        self.draw_field_border(2, 1, height - 10, width - 2, "Content", content_active)
        self.draw_content()
        
        context_y = height - 7
        context_active = self.active_field == Field.CONTEXT
        self.stdscr.addstr(context_y, 2, "Context:", 
                          curses.color_pair(1) if context_active else 0)
        self.draw_context()
        
        tags_y = context_y + 1
        tags_active = self.active_field == Field.TAGS
        self.stdscr.addstr(tags_y, 2, "Tags:", 
                          curses.color_pair(1) if tags_active else 0)
        self.draw_tags()
        
        help_y = height - 2
        help_text = "Ctrl+S Save  ESC Cancel  Tab Next Field  F1 Help"
        self.stdscr.addstr(help_y, (width - len(help_text)) // 2, help_text,
                          curses.color_pair(5))
        
        self.position_cursor()
        
        self.stdscr.refresh()
    
    def draw_field_border(self, y: int, x: int, height: int, width: int, 
                         title: str, active: bool):
        """Draw a border around a field."""
        attr = curses.color_pair(1) if active else 0
        
        self.stdscr.addch(y, x, curses.ACS_ULCORNER, attr)
        self.stdscr.addstr(y, x + 1, f" {title} ", attr | curses.A_BOLD)
        for i in range(len(title) + 3, width - 1):
            self.stdscr.addch(y, x + i, curses.ACS_HLINE, attr)
        self.stdscr.addch(y, x + width - 1, curses.ACS_URCORNER, attr)
        
        for i in range(1, height - 1):
            self.stdscr.addch(y + i, x, curses.ACS_VLINE, attr)
            self.stdscr.addch(y + i, x + width - 1, curses.ACS_VLINE, attr)
        
        self.stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER, attr)
        for i in range(1, width - 1):
            self.stdscr.addch(y + height - 1, x + i, curses.ACS_HLINE, attr)
        self.stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER, attr)
    
    def draw_content(self):
        """Draw the content area with text and cursor."""
        if not self.content_win:
            return
        
        self.content_win.clear()
        
        lines = self.content.split('\n')
        win_height, win_width = self.content_win.getmaxyx()
        
        for i, line in enumerate(lines[self.content_scroll:]):
            if i >= win_height - 1:
                break
            
            display_line = line[:win_width - 1] if len(line) >= win_width else line
            self.content_win.addstr(i, 0, display_line)
        
        self.content_win.refresh()
    
    def draw_context(self):
        """Draw the context field."""
        if not self.context_win:
            return
        
        self.context_win.clear()
        win_height, win_width = self.context_win.getmaxyx()
        
        display_text = self.context[:win_width - 1] if len(self.context) >= win_width else self.context
        self.context_win.addstr(0, 0, display_text)
        self.context_win.refresh()
    
    def draw_tags(self):
        """Draw the tags field."""
        if not self.tags_win:
            return
        
        self.tags_win.clear()
        win_height, win_width = self.tags_win.getmaxyx()
        
        display_text = self.tags[:win_width - 1] if len(self.tags) >= win_width else self.tags
        self.tags_win.addstr(0, 0, display_text)
        self.tags_win.refresh()
    
    def draw_sources(self):
        """Draw the sources field."""
        if not self.sources_win:
            return
        
        self.sources_win.clear()
        self.sources_win.addstr(0, 0, self.sources[:self.sources_win.getmaxyx()[1] - 1])
        self.sources_win.refresh()
    
    def draw_idea_list(self):
        """Draw the idea list in browse mode."""
        if not self.idea_list_win:
            return
        
        self.idea_list_win.clear()
        height, width = self.idea_list_win.getmaxyx()
        
        if not self.idea_files:
            self.idea_files = self.writer.list_ideas()
        
        if not self.idea_files:
            self.idea_list_win.addstr(1, 1, "No ideas found. Press ESC to return to capture mode.")
        else:
            for i, idea_file in enumerate(self.idea_files[:height - 2]):
                attr = curses.color_pair(1) if i == self.selected_idea_index else 0
                
                idea_data = self.writer.read_idea_file(idea_file)
                if idea_data:
                    timestamp = idea_data['frontmatter'].get('timestamp', 'Unknown')
                    content_preview = idea_data['body'][:50].replace('\n', ' ') + "..."
                    display_text = f"{timestamp[:19]} - {content_preview}"
                else:
                    display_text = f"{idea_file.name}"
                
                if len(display_text) > width - 4:
                    display_text = display_text[:width - 7] + "..."
                
                self.idea_list_win.addstr(i + 1, 1, display_text, attr)
        
        self.idea_list_win.refresh()
    
    def draw_help(self):
        """Draw the help overlay."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        for y in range(height):
            self.stdscr.addstr(y, 0, " " * width, curses.color_pair(5))
        
        help_text = HelpDisplay.get_help_text()
        lines = help_text.split('\n')
        
        start_y = max(0, (height - len(lines)) // 2)
        for i, line in enumerate(lines):
            if start_y + i >= height - 1:
                break
            
            x = max(0, (width - len(line)) // 2)
            self.stdscr.addstr(start_y + i, x, line[:width - 1], curses.color_pair(5))
        
        self.stdscr.refresh()
    
    def position_cursor(self):
        """Position the cursor in the active field."""
        if self.active_field == Field.CONTENT:
            lines = self.content[:self.content_cursor].split('\n')
            cursor_line = len(lines) - 1 - self.content_scroll
            cursor_col = len(lines[-1]) if lines else 0
            
            if 0 <= cursor_line < self.content_win.getmaxyx()[0]:
                self.content_win.move(cursor_line, min(cursor_col, self.content_win.getmaxyx()[1] - 1))
        
        elif self.active_field == Field.CONTEXT:
            cursor_col = min(self.context_cursor, self.context_win.getmaxyx()[1] - 1)
            self.context_win.move(0, cursor_col)
        
        elif self.active_field == Field.TAGS:
            cursor_col = min(self.tags_cursor, self.tags_win.getmaxyx()[1] - 1)
            self.tags_win.move(0, cursor_col)
        
        elif self.active_field == Field.SOURCES:
            cursor_col = min(self.sources_cursor, self.sources_win.getmaxyx()[1] - 1)
            self.sources_win.move(0, cursor_col)
    
    def run_capture(self, mode: str = "quick") -> bool:
        """Run the capture interface and return True if saved."""
        try:
            if mode == "clipboard":
                self.capture_clipboard_content()
                self.active_modalities.add("clipboard")
            elif mode == "screenshot":
                self.capture_screenshot()
                self.active_modalities.add("screenshot")
            elif mode == "voice":
                self.active_modalities = {"audio"}
            elif mode == "multimodal":
                self.active_modalities = {"text", "clipboard"}
            
            return curses.wrapper(self._run_ui_loop)
            
        except KeyboardInterrupt:
            return False
        except Exception as e:
            print(f"Error in capture UI: {e}")
            return False
    
    def _run_ui_loop(self, stdscr) -> bool:
        """Main UI loop."""
        self.initialize_ui(stdscr)
        
        while True:
            self.draw_ui()
            
            try:
                key = stdscr.getch()
                
                if key == curses.KEY_F1:
                    self.show_help = not self.show_help
                    continue
                
                if self.show_help:
                    self.show_help = False
                    continue
                
                should_continue = self.keybindings.handle_key(key)
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                return False
        
        return True
    
    def set_active_field(self, field: Field):
        """Set the active field."""
        self.active_field = field
    
    def insert_char(self, char: str):
        """Insert character at cursor in content."""
        self.content = (self.content[:self.content_cursor] + 
                       char + 
                       self.content[self.content_cursor:])
        self.content_cursor += 1
    
    def insert_newline(self):
        """Insert newline in content."""
        self.insert_char('\n')
    
    def delete_char_before(self):
        """Delete character before cursor in content."""
        if self.content_cursor > 0:
            self.content = (self.content[:self.content_cursor - 1] + 
                           self.content[self.content_cursor:])
            self.content_cursor -= 1
    
    def delete_char_after(self):
        """Delete character after cursor in content."""
        if self.content_cursor < len(self.content):
            self.content = (self.content[:self.content_cursor] + 
                           self.content[self.content_cursor + 1:])
    
    def move_cursor_left(self):
        """Move cursor left in content."""
        if self.content_cursor > 0:
            self.content_cursor -= 1
    
    def move_cursor_right(self):
        """Move cursor right in content."""
        if self.content_cursor < len(self.content):
            self.content_cursor += 1
    
    def move_cursor_up(self):
        """Move cursor up in content."""
        lines = self.content[:self.content_cursor].split('\n')
        if len(lines) > 1:
            current_line_pos = len(lines[-1])
            prev_line_len = len(lines[-2]) if len(lines) > 1 else 0
            new_pos = min(current_line_pos, prev_line_len)
            self.content_cursor -= len(lines[-1]) + 1 - new_pos
    
    def move_cursor_down(self):
        """Move cursor down in content."""
        remaining = self.content[self.content_cursor:]
        lines = remaining.split('\n')
        if len(lines) > 1:
            current_line_pos = len(self.content[:self.content_cursor].split('\n')[-1])
            next_line_len = len(lines[1])
            new_pos = min(current_line_pos, next_line_len)
            self.content_cursor += len(lines[0]) + 1 + new_pos - current_line_pos
    
    def move_cursor_home(self):
        """Move cursor to beginning of line."""
        lines = self.content[:self.content_cursor].split('\n')
        if lines:
            self.content_cursor -= len(lines[-1])
    
    def move_cursor_end(self):
        """Move cursor to end of line."""
        remaining = self.content[self.content_cursor:]
        newline_pos = remaining.find('\n')
        if newline_pos == -1:
            self.content_cursor = len(self.content)
        else:
            self.content_cursor += newline_pos
    
    def clear_line(self):
        """Clear current line in content."""
        lines_before = self.content[:self.content_cursor].split('\n')
        lines_after = self.content[self.content_cursor:].split('\n')
        
        if lines_before:
            lines_before[-1] = ""
        
        self.content = '\n'.join(lines_before + lines_after[1:])
        self.move_cursor_home()
    
    def delete_word_before(self):
        """Delete word before cursor."""
        if self.content_cursor == 0:
            return
        
        pos = self.content_cursor - 1
        while pos > 0 and self.content[pos].isspace():
            pos -= 1
        while pos > 0 and not self.content[pos - 1].isspace():
            pos -= 1
        
        self.content = self.content[:pos] + self.content[self.content_cursor:]
        self.content_cursor = pos
    
    def scroll_up(self):
        """Scroll content area up."""
        if self.content_scroll > 0:
            self.content_scroll -= 1
    
    def scroll_down(self):
        """Scroll content area down."""
        lines = self.content.split('\n')
        max_scroll = max(0, len(lines) - self.content_win.getmaxyx()[0] + 1)
        if self.content_scroll < max_scroll:
            self.content_scroll += 1
    
    def insert_context_char(self, char: str):
        """Insert character in context field."""
        self.context = (self.context[:self.context_cursor] + 
                       char + 
                       self.context[self.context_cursor:])
        self.context_cursor += 1
    
    def delete_context_char_before(self):
        """Delete character before cursor in context."""
        if self.context_cursor > 0:
            self.context = (self.context[:self.context_cursor - 1] + 
                           self.context[self.context_cursor:])
            self.context_cursor -= 1
    
    def delete_context_char_after(self):
        """Delete character after cursor in context."""
        if self.context_cursor < len(self.context):
            self.context = (self.context[:self.context_cursor] + 
                           self.context[self.context_cursor + 1:])
    
    def move_context_cursor_left(self):
        """Move cursor left in context."""
        if self.context_cursor > 0:
            self.context_cursor -= 1
    
    def move_context_cursor_right(self):
        """Move cursor right in context."""
        if self.context_cursor < len(self.context):
            self.context_cursor += 1
    
    def move_context_cursor_home(self):
        """Move cursor to beginning of context."""
        self.context_cursor = 0
    
    def move_context_cursor_end(self):
        """Move cursor to end of context."""
        self.context_cursor = len(self.context)
    
    def clear_context(self):
        """Clear context field."""
        self.context = ""
        self.context_cursor = 0
    
    def delete_context_word_before(self):
        """Delete word before cursor in context."""
        if self.context_cursor == 0:
            return
        
        pos = self.context_cursor - 1
        while pos > 0 and self.context[pos].isspace():
            pos -= 1
        while pos > 0 and not self.context[pos - 1].isspace():
            pos -= 1
        
        self.context = self.context[:pos] + self.context[self.context_cursor:]
        self.context_cursor = pos
    
    def insert_tags_char(self, char: str):
        """Insert character in tags field."""
        self.tags = (self.tags[:self.tags_cursor] + 
                    char + 
                    self.tags[self.tags_cursor:])
        self.tags_cursor += 1
    
    def delete_tags_char_before(self):
        """Delete character before cursor in tags."""
        if self.tags_cursor > 0:
            self.tags = (self.tags[:self.tags_cursor - 1] + 
                        self.tags[self.tags_cursor:])
            self.tags_cursor -= 1
    
    def delete_tags_char_after(self):
        """Delete character after cursor in tags."""
        if self.tags_cursor < len(self.tags):
            self.tags = (self.tags[:self.tags_cursor] + 
                        self.tags[self.tags_cursor + 1:])
    
    def move_tags_cursor_left(self):
        """Move cursor left in tags."""
        if self.tags_cursor > 0:
            self.tags_cursor -= 1
    
    def move_tags_cursor_right(self):
        """Move cursor right in tags."""
        if self.tags_cursor < len(self.tags):
            self.tags_cursor += 1
    
    def move_tags_cursor_home(self):
        """Move cursor to beginning of tags."""
        self.tags_cursor = 0
    
    def move_tags_cursor_end(self):
        """Move cursor to end of tags."""
        self.tags_cursor = len(self.tags)
    
    def clear_tags(self):
        """Clear tags field."""
        self.tags = ""
        self.tags_cursor = 0
    
    def delete_tags_word_before(self):
        """Delete word before cursor in tags."""
        if self.tags_cursor == 0:
            return
        
        pos = self.tags_cursor - 1
        while pos > 0 and self.tags[pos].isspace():
            pos -= 1
        while pos > 0 and not self.tags[pos - 1].isspace():
            pos -= 1
        
        self.tags = self.tags[:pos] + self.tags[self.tags_cursor:]
        self.tags_cursor = pos
    
    def insert_sources_char(self, char: str):
        """Insert character in sources field."""
        self.sources = (self.sources[:self.sources_cursor] + 
                       char + 
                       self.sources[self.sources_cursor:])
        self.sources_cursor += 1
    
    def delete_sources_char_before(self):
        """Delete character before cursor in sources field."""
        if self.sources_cursor > 0:
            self.sources = (self.sources[:self.sources_cursor-1] + 
                           self.sources[self.sources_cursor:])
            self.sources_cursor -= 1
    
    def delete_sources_char_after(self):
        """Delete character after cursor in sources field."""
        if self.sources_cursor < len(self.sources):
            self.sources = (self.sources[:self.sources_cursor] + 
                           self.sources[self.sources_cursor+1:])
    
    def move_sources_cursor_left(self):
        """Move cursor left in sources field."""
        self.sources_cursor = max(0, self.sources_cursor - 1)
    
    def move_sources_cursor_right(self):
        """Move cursor right in sources field."""
        self.sources_cursor = min(len(self.sources), self.sources_cursor + 1)
    
    def move_sources_cursor_home(self):
        """Move cursor to beginning of sources field."""
        self.sources_cursor = 0
    
    def move_sources_cursor_end(self):
        """Move cursor to end of sources field."""
        self.sources_cursor = len(self.sources)
    
    def clear_sources(self):
        """Clear sources field."""
        self.sources = ""
        self.sources_cursor = 0
    
    def delete_sources_word_before(self):
        """Delete word before cursor in sources field."""
        if self.sources_cursor == 0:
            return
        
        pos = self.sources_cursor - 1
        while pos > 0 and self.sources[pos].isspace():
            pos -= 1
        while pos > 0 and not self.sources[pos-1].isspace():
            pos -= 1
        
        self.sources = self.sources[:pos] + self.sources[self.sources_cursor:]
        self.sources_cursor = pos
    
    def toggle_capture_mode(self):
        """Toggle between capture modes."""
        if "text" in self.active_modalities:
            self.active_modalities = {"clipboard"}
        elif "clipboard" in self.active_modalities:
            self.active_modalities = {"screenshot"}
        elif "screenshot" in self.active_modalities:
            self.active_modalities = {"audio"}
        else:
            self.active_modalities = {"text"}
    
    def next_modality(self):
        """Move to next modality in selection."""
        self.modality_index = (self.modality_index + 1) % len(self.available_modalities)
    
    def prev_modality(self):
        """Move to previous modality in selection."""
        self.modality_index = (self.modality_index - 1) % len(self.available_modalities)
    
    def toggle_current_modality(self):
        """Toggle the currently selected modality."""
        modality = self.available_modalities[self.modality_index]
        if modality in self.active_modalities:
            self.active_modalities.discard(modality)
        else:
            self.active_modalities.add(modality)
    
    def toggle_modality_by_index(self, index: int):
        """Toggle modality by index."""
        if 0 <= index < len(self.available_modalities):
            modality = self.available_modalities[index]
            if modality in self.active_modalities:
                self.active_modalities.discard(modality)
            else:
                self.active_modalities.add(modality)
    
    def capture_clipboard_content(self):
        """Capture current clipboard content."""
        try:
            result = subprocess.run(['wl-paste', '-t', 'text'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                self.capture_data['clipboard'] = result.stdout.strip()
                return
            
            result = subprocess.run(['wl-paste', '-l'], 
                                  capture_output=True, text=True, timeout=2)
            if 'image/' in result.stdout:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                image_path = self.writer.media_dir / f"{timestamp}_clipboard.png"
                
                with image_path.open('wb') as f:
                    subprocess.run(['wl-paste', '-t', 'image/png'], stdout=f, timeout=5)
                
                if not hasattr(self.capture_data, 'media_files'):
                    self.capture_data['media_files'] = []
                self.capture_data['media_files'].append({
                    'type': 'image',
                    'path': str(image_path)
                })
        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
            pass  # Ignore clipboard errors
    
    def capture_screenshot(self):
        """Capture screenshot."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            screenshot_path = self.writer.media_dir / f"{timestamp}_screenshot.png"
            
            result = subprocess.run(['grim', str(screenshot_path)], 
                                  capture_output=True, timeout=10)
            
            if result.returncode == 0:
                if not hasattr(self.capture_data, 'media_files'):
                    self.capture_data['media_files'] = []
                self.capture_data['media_files'].append({
                    'type': 'screenshot',
                    'path': str(screenshot_path)
                })
        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
            pass  # Ignore screenshot errors
    
    def save_capture(self):
        """Save the current capture."""
        try:
            active = set(self.active_modalities)
            if not active:
                self.show_error("Nothing to save: no modality selected")
                return

            text_has_content = bool(self.content.strip())

            has_clipboard = bool(self.capture_data.get('clipboard', '').strip())
            has_media = bool(self.capture_data.get('media_files'))

            if 'clipboard' in active and not has_clipboard:
                self.capture_clipboard_content()
                has_clipboard = bool(self.capture_data.get('clipboard', '').strip())

            if 'screenshot' in active and not has_media:
                self.capture_screenshot()
                has_media = bool(self.capture_data.get('media_files'))

            if not (text_has_content or has_clipboard or has_media):
                self.show_error("Nothing to save: provide content or captured data")
                return

            location = get_device_location()
            capture_data = {
                'timestamp': datetime.now(),
                'content': self.content.strip(),
                'context': {'activity': self.context.strip()} if self.context.strip() else {},
                'tags': [tag.strip() for tag in self.tags.split(',') if tag.strip()],
                'sources': [source.strip() for source in self.sources.split(',') if source.strip()],
                'location': location,
                'modalities': list(self.active_modalities),
                **self.capture_data
            }

            if 'clipboard' in active and 'clipboard' in self.capture_data:
                capture_data['clipboard'] = self.capture_data['clipboard']

            if 'media_files' in self.capture_data:
                capture_data['media_files'] = self.capture_data['media_files']

            result_file = self.writer.write_capture(capture_data)

            try:
                subprocess.run(['notify-send', '-t', '2000', '-u', 'normal',
                              '-i', 'dialog-information', 'Capture Success',
                              f'Idea saved to {result_file.name}'], timeout=5)
            except Exception:
                pass

        except Exception as e:
            self.show_error(f"Error saving: {e}")
    
    def cancel_capture(self):
        """Cancel the capture without saving."""
        pass  # Just exit
    
    def show_error(self, message: str):
        """Show error notification and on-screen message."""
        try:
            subprocess.run(['notify-send', '-t', '2000', '-u', 'critical', 
                          '-i', 'dialog-error', 'Capture Failure', message], 
                         timeout=5)
        except Exception:
            pass
        
        if self.stdscr:
            self.stdscr.addstr(0, 0, f"Error: {message}", curses.color_pair(4))
            self.stdscr.refresh()
            curses.napms(2000)
    
    def enter_browse_mode(self):
        """Enter browse mode to view existing ideas."""
        self.ui_mode = UIMode.BROWSE
        self.active_field = Field.IDEA_LIST
        self.idea_files = self.writer.list_ideas()
        self.selected_idea_index = 0
        self.create_windows()
        self.keybindings.set_mode(UIMode.BROWSE)
    
    def enter_edit_mode(self):
        """Enter edit mode with selected idea."""
        if self.idea_files and 0 <= self.selected_idea_index < len(self.idea_files):
            idea_file = self.idea_files[self.selected_idea_index]
            if self.load_idea_for_editing(idea_file):
                self.ui_mode = UIMode.EDIT
                self.active_field = Field.CONTENT
                self.current_idea_file = idea_file
                self.create_windows()
                self.keybindings.set_mode(UIMode.EDIT)
    
    def load_idea_for_editing(self, idea_file: Path) -> bool:
        """Load an existing idea file for editing."""
        try:
            idea_data = self.writer.read_idea_file(idea_file)
            if idea_data:
                frontmatter = idea_data['frontmatter']
                body = idea_data['body']
                
                self.content = self.extract_content_section(body)
                self.context = frontmatter.get('context', {}).get('activity', '')
                self.tags = ', '.join(frontmatter.get('tags', []))
                self.sources = ', '.join(frontmatter.get('sources', []))
                self.active_modalities = set(frontmatter.get('modalities', ['text']))
                
                return True
        except Exception as e:
            self.show_error(f"Failed to load idea: {e}")
        return False
    
    def extract_content_section(self, body: str) -> str:
        """Extract content from markdown body."""
        lines = body.split('\n')
        content_lines = []
        in_content = False
        
        for line in lines:
            if line.strip() == "## Content":
                in_content = True
                continue
            elif line.startswith("## ") and in_content:
                break
            elif in_content:
                content_lines.append(line)
        
        return '\n'.join(content_lines).strip()
    
    def next_idea(self):
        """Navigate to next idea in browse mode."""
        if self.idea_files:
            self.selected_idea_index = min(len(self.idea_files) - 1, self.selected_idea_index + 1)
    
    def prev_idea(self):
        """Navigate to previous idea in browse mode."""
        self.selected_idea_index = max(0, self.selected_idea_index - 1)
    
    def select_idea_for_editing(self):
        """Select current idea for editing."""
        self.enter_edit_mode()
    
    def show_help(self):
        """Toggle help display."""
        self.show_help = not self.show_help


class CaptureDaemon:
    """Background daemon that handles capture requests."""
    
    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.socket_path = self.config['daemon']['socket_path']
        self.running = False
        self.server_socket = None
        
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                'vault': {'path': '~/notes', 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
                'daemon': {'socket_path': '/tmp/capture_daemon.sock', 'auto_start': True, 'hot_reload': True},
                'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True}
            }
    
    def start(self):
        """Start the daemon."""
        self.cleanup_socket()
        
        try:
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_socket.bind(self.socket_path)
            self.server_socket.listen(5)
            
            self.running = True
            print(f"Capture daemon started on {self.socket_path}")
            
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    threading.Thread(target=self.handle_client, args=(client_socket,)).start()
                except OSError:
                    if self.running:
                        print("Socket error, stopping daemon")
                    break
                    
        except Exception as e:
            print(f"Error starting daemon: {e}")
        finally:
            self.cleanup()
    
    def handle_client(self, client_socket):
        """Handle client request."""
        try:
            data = client_socket.recv(1024).decode('utf-8')
            command = json.loads(data)
            
            action = command.get('action', 'show_capture')
            mode = command.get('mode', 'quick')
            
            if action == 'show_capture':
                self.show_capture_ui(mode)
                client_socket.send(b'OK')
            elif action == 'status':
                client_socket.send(b'OK')
            elif action == 'stop':
                client_socket.send(b'OK')
                self.running = False
            else:
                client_socket.send(b'ERROR')
                
        except Exception as e:
            print(f"Error handling client: {e}")
            client_socket.send(b'ERROR')
        finally:
            client_socket.close()
    
    def show_capture_ui(self, mode: str):
        """Show the capture UI."""
        try:
            ui = CaptureUI(self.config)
            ui.run_capture(mode)
        except Exception as e:
            print(f"Error showing capture UI: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()
    
    def cleanup_socket(self):
        """Clean up existing socket file."""
        try:
            os.unlink(self.socket_path)
        except FileNotFoundError:
            pass
    
    def cleanup(self):
        """Clean up resources."""
        self.cleanup_socket()
        if self.server_socket:
            self.server_socket.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Terminal Capture Daemon')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--vault-path', help='Vault path override')
    parser.add_argument('--socket-path', help='Socket path override')
    parser.add_argument('--mode', default='quick', help='Capture mode for direct UI')
    
    args = parser.parse_args()
    
    if args.daemon:
        daemon = CaptureDaemon(args.config)
        
        if args.vault_path:
            daemon.config['vault']['path'] = args.vault_path
        if args.socket_path:
            daemon.config['daemon']['socket_path'] = args.socket_path
            daemon.socket_path = args.socket_path
        
        daemon.start()
    else:
        config = {
            'vault': {'path': args.vault_path or '~/notes', 'capture_dir': 'capture/raw_capture', 'media_dir': 'capture/raw_capture/media'},
            'daemon': {'socket_path': args.socket_path or '/tmp/capture_daemon.sock'},
            'ui': {'theme': 'default', 'window_size': [80, 24], 'auto_focus_content': True}
        }
        
        ui = CaptureUI(config)
        success = ui.run_capture(args.mode)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
