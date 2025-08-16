#!/usr/bin/env python3
"""
Semantic keybinding handler for the terminal capture UI.
Provides vim-inspired but intuitive keybindings.
"""

import curses
import os
from typing import Dict, Callable, Optional, Any
from enum import Enum


class UIMode(Enum):
    """UI interaction modes."""
    NORMAL = "normal"
    INSERT = "insert"
    COMMAND = "command"
    BROWSE = "browse"
    EDIT = "edit"


class Field(Enum):
    """UI fields that can be focused."""
    CONTENT = "content"
    CONTEXT = "context"
    TAGS = "tags"
    SOURCES = "sources"
    MODALITIES = "modalities"
    IDEA_LIST = "idea_list"


class SemanticKeybindings:
    """Handles semantic keybindings for the capture UI."""
    
    def __init__(self, ui_handler):
        self.ui = ui_handler
        self.mode = UIMode.INSERT
        self.current_field = Field.CONTENT
        
        self.key_map = {
            curses.KEY_UP: 'up',
            curses.KEY_DOWN: 'down',
            curses.KEY_LEFT: 'left',
            curses.KEY_RIGHT: 'right',
            curses.KEY_HOME: 'home',
            curses.KEY_END: 'end',
            curses.KEY_PPAGE: 'page_up',
            curses.KEY_NPAGE: 'page_down',
            curses.KEY_BACKSPACE: 'backspace',
            curses.KEY_DC: 'delete',
            curses.KEY_F1: 'f1',
            9: 'tab',
            27: 'escape',
            10: 'enter',
            13: 'enter',
        }
        
        self.ctrl_keys = {
            1: 'ctrl+a',    # Ctrl+A
            2: 'ctrl+b',    # Ctrl+B
            5: 'ctrl+e',    # Ctrl+E
            19: 'ctrl+s',   # Ctrl+S
            21: 'ctrl+u',   # Ctrl+U
            23: 'ctrl+w',   # Ctrl+W
            13: 'ctrl+m',   # Ctrl+M
        }
    
    def handle_key(self, key: int) -> bool:
        """
        Handle a key press and return True if the UI should continue.
        Returns False if the capture should be cancelled or saved.
        """
        key_str = self.get_key_string(key)
        
        if key_str == 'escape':
            return self.handle_cancel()
        elif key_str == 'ctrl+s':
            return self.handle_save()
        elif key_str == 'ctrl+b':
            return self.handle_browse_mode()
        elif key_str == 'ctrl+e' and self.mode == UIMode.BROWSE:
            return self.handle_edit_mode()
        elif key_str == 'f1':
            return self.handle_help()
        elif key_str == 'tab':
            return self.handle_next_field()
        elif key_str == 'shift+tab':
            return self.handle_prev_field()
        
        if isinstance(key, int) and ord('1') <= key <= ord('9'):
            self.ui.toggle_modality_by_index(key - ord('1'))
            return True
        
        if self.current_field == Field.CONTENT:
            return self.handle_content_key(key_str, key)
        elif self.current_field == Field.CONTEXT:
            return self.handle_context_key(key_str, key)
        elif self.current_field == Field.TAGS:
            return self.handle_tags_key(key_str, key)
        elif self.current_field == Field.SOURCES:
            return self.handle_sources_key(key_str, key)
        elif self.current_field == Field.MODALITIES:
            return self.handle_modalities_key(key_str, key)
        elif self.current_field == Field.IDEA_LIST:
            return self.handle_idea_list_key(key_str, key)
        
        return True
    
    def get_key_string(self, key: int) -> str:
        """Convert key code to string representation."""
        if key in self.ctrl_keys:
            return self.ctrl_keys[key]
        
        if key in self.key_map:
            return self.key_map[key]
        
        if key == curses.KEY_BTAB:
            return 'shift+tab'
        
        if 32 <= key <= 126:
            return chr(key)
        
        if key == ord('h'):
            return 'left' if self.mode == UIMode.NORMAL else chr(key)
        elif key == ord('j'):
            return 'down' if self.mode == UIMode.NORMAL else chr(key)
        elif key == ord('k'):
            return 'up' if self.mode == UIMode.NORMAL else chr(key)
        elif key == ord('l'):
            return 'right' if self.mode == UIMode.NORMAL else chr(key)
        
        return f'unknown_{key}'
    
    def handle_content_key(self, key_str: str, raw_key: int) -> bool:
        """Handle keys in the content field."""
        if key_str == 'up':
            self.ui.move_cursor_up()
        elif key_str == 'down':
            self.ui.move_cursor_down()
        elif key_str == 'left':
            self.ui.move_cursor_left()
        elif key_str == 'right':
            self.ui.move_cursor_right()
        elif key_str == 'home' or key_str == 'ctrl+a':
            self.ui.move_cursor_home()
        elif key_str == 'end' or key_str == 'ctrl+e':
            self.ui.move_cursor_end()
        elif key_str == 'page_up':
            self.ui.scroll_up()
        elif key_str == 'page_down':
            self.ui.scroll_down()
        elif key_str == 'backspace':
            self.ui.delete_char_before()
        elif key_str == 'delete':
            self.ui.delete_char_after()
        elif key_str == 'ctrl+u':
            self.ui.clear_line()
        elif key_str == 'ctrl+w':
            self.ui.delete_word_before()
        elif key_str == 'enter':
            self.ui.insert_newline()
        elif key_str == 'space':
            if self.mode == UIMode.NORMAL:
                self.ui.toggle_capture_mode()
            else:
                self.ui.insert_char(' ')
        elif len(key_str) == 1 and key_str.isprintable():
            self.ui.insert_char(key_str)
        
        return True
    
    def handle_context_key(self, key_str: str, raw_key: int) -> bool:
        """Handle keys in the context field."""
        if key_str == 'left':
            self.ui.move_context_cursor_left()
        elif key_str == 'right':
            self.ui.move_context_cursor_right()
        elif key_str == 'home' or key_str == 'ctrl+a':
            self.ui.move_context_cursor_home()
        elif key_str == 'end' or key_str == 'ctrl+e':
            self.ui.move_context_cursor_end()
        elif key_str == 'backspace':
            self.ui.delete_context_char_before()
        elif key_str == 'delete':
            self.ui.delete_context_char_after()
        elif key_str == 'ctrl+u':
            self.ui.clear_context()
        elif key_str == 'ctrl+w':
            self.ui.delete_context_word_before()
        elif key_str == 'enter':
            self.handle_next_field()
        elif len(key_str) == 1 and key_str.isprintable():
            self.ui.insert_context_char(key_str)
        
        return True
    
    def handle_tags_key(self, key_str: str, raw_key: int) -> bool:
        """Handle keys in the tags field."""
        if key_str == 'left':
            self.ui.move_tags_cursor_left()
        elif key_str == 'right':
            self.ui.move_tags_cursor_right()
        elif key_str == 'home' or key_str == 'ctrl+a':
            self.ui.move_tags_cursor_home()
        elif key_str == 'end' or key_str == 'ctrl+e':
            self.ui.move_tags_cursor_end()
        elif key_str == 'backspace':
            self.ui.delete_tags_char_before()
        elif key_str == 'delete':
            self.ui.delete_tags_char_after()
        elif key_str == 'ctrl+u':
            self.ui.clear_tags()
        elif key_str == 'ctrl+w':
            self.ui.delete_tags_word_before()
        elif key_str == 'enter':
            self.handle_next_field()
        elif len(key_str) == 1 and key_str.isprintable():
            self.ui.insert_tags_char(key_str)
        
        return True
    
    def handle_modalities_key(self, key_str: str, raw_key: int) -> bool:
        """Handle keys in the modalities field."""
        if key_str == 'left':
            self.ui.prev_modality()
        elif key_str == 'right':
            self.ui.next_modality()
        elif key_str == 'space' or key_str == 'enter':
            self.ui.toggle_current_modality()
        elif key_str.isdigit():
            modality_index = int(key_str) - 1
            self.ui.toggle_modality_by_index(modality_index)
        
        return True
    
    def handle_sources_key(self, key_str: str, raw_key: int) -> bool:
        """Handle keys in the sources field."""
        if key_str == 'left':
            self.ui.move_sources_cursor_left()
        elif key_str == 'right':
            self.ui.move_sources_cursor_right()
        elif key_str == 'home' or key_str == 'ctrl+a':
            self.ui.move_sources_cursor_home()
        elif key_str == 'end' or key_str == 'ctrl+e':
            self.ui.move_sources_cursor_end()
        elif key_str == 'backspace':
            self.ui.delete_sources_char_before()
        elif key_str == 'delete':
            self.ui.delete_sources_char_after()
        elif key_str == 'ctrl+u':
            self.ui.clear_sources()
        elif key_str == 'ctrl+w':
            self.ui.delete_sources_word_before()
        elif key_str == 'enter':
            self.handle_next_field()
        elif len(key_str) == 1 and key_str.isprintable():
            self.ui.insert_sources_char(key_str)
        
        return True
    
    def handle_idea_list_key(self, key_str: str, raw_key: int) -> bool:
        """Handle keys in the idea list field."""
        if key_str == 'up':
            self.ui.prev_idea()
        elif key_str == 'down':
            self.ui.next_idea()
        elif key_str == 'enter':
            self.ui.select_idea_for_editing()
        elif key_str == 'ctrl+e':
            return self.handle_edit_mode()
        
        return True
    
    def handle_browse_mode(self) -> bool:
        """Handle browse mode command (Ctrl+B)."""
        self.ui.enter_browse_mode()
        return True
    
    def handle_edit_mode(self) -> bool:
        """Handle edit mode command (Ctrl+E in browse mode)."""
        if self.mode == UIMode.BROWSE:
            self.ui.enter_edit_mode()
        return True
    
    def handle_save(self) -> bool:
        """Handle save command (Ctrl+S)."""
        if os.environ.get("KMS_DEBUG_SAVE") == "1":
            print("[KMS_DEBUG] Ctrl+S received; invoking save_capture()", flush=True)
        self.ui.save_capture()
        if os.environ.get("KMS_DEBUG_SAVE") == "1":
            print("[KMS_DEBUG] save_capture() returned; exiting loop", flush=True)
        return False  # Exit the input loop
    
    def handle_cancel(self) -> bool:
        """Handle cancel command (ESC)."""
        self.ui.cancel_capture()
        return False  # Exit the input loop
    
    def handle_help(self) -> bool:
        """Handle help command (F1)."""
        self.ui.show_help()
        return True
    def handle_next_field(self) -> bool:
        """Handle next field navigation (Tab)."""
        fields = list(Field)
        current_index = fields.index(self.current_field)
        next_index = (current_index + 1) % len(fields)
        self.current_field = fields[next_index]
        self.ui.set_active_field(self.current_field)
        return True
    
    def handle_prev_field(self) -> bool:
        """Handle previous field navigation (Shift+Tab)."""
        fields = list(Field)
        current_index = fields.index(self.current_field)
        prev_index = (current_index - 1) % len(fields)
        self.current_field = fields[prev_index]
        self.ui.set_active_field(self.current_field)
        return True
    
    def set_mode(self, mode: UIMode):
        """Set the current UI mode."""
        self.mode = mode
    
    def get_current_field(self) -> Field:
        """Get the currently active field."""
        return self.current_field
    
    def set_current_field(self, field: Field):
        """Set the currently active field."""
        self.current_field = field


class HelpDisplay:
    """Displays help information for keybindings."""
    
    @staticmethod
    def get_help_text() -> str:
        """Get formatted help text for keybindings."""
        return """
TERMINAL CAPTURE DAEMON - KEYBINDINGS HELP

GLOBAL ACTIONS:
  Ctrl+S          Save capture and exit
  ESC             Cancel capture without saving
  Ctrl+B          Enter browse mode
  Ctrl+E          Enter edit mode (from browse)
  F1              Show/hide this help
  Tab             Next field
  Shift+Tab       Previous field

CONTENT FIELD:
  ↑↓←→ / hjkl     Navigate cursor
  Home / Ctrl+A   Beginning of line
  End / Ctrl+E    End of line
  Page Up/Down    Scroll content area
  Backspace       Delete character before cursor
  Delete          Delete character after cursor
  Ctrl+U          Clear current line
  Ctrl+W          Delete word before cursor
  Enter           New line
  Space           Insert space (or toggle mode in normal mode)

CONTEXT FIELD:
  ←→              Navigate cursor
  Home/End        Beginning/end of field
  Backspace/Del   Delete characters
  Ctrl+U          Clear field
  Enter           Move to next field

TAGS FIELD:
  ←→              Navigate cursor
  Home/End        Beginning/end of field
  Backspace/Del   Delete characters
  Ctrl+U          Clear field
  Enter           Move to next field

SOURCES FIELD:
  ←→              Navigate cursor
  Home/End        Beginning/end of field
  Backspace/Del   Delete characters
  Ctrl+U          Clear field
  Enter           Move to next field
  
MODALITIES FIELD:
  ←→              Navigate between options
  Space/Enter     Toggle current modality
  1-9 / Ctrl+1-9  Toggle modality by number

BROWSE MODE:
  ↑↓              Navigate idea list
  Enter           Select idea for editing
  Ctrl+E          Edit selected idea
  ESC             Return to capture mode

Press any key to close help...
"""


if __name__ == "__main__":
    print("Testing keybinding system...")
    print(HelpDisplay.get_help_text())
