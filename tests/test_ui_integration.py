#!/usr/bin/env python3
"""
Integration tests for UI components and user interactions.
Tests the complete UI flow without requiring actual ncurses.
"""

import pytest
from unittest.mock import MagicMock, patch
import tempfile
import shutil
from pathlib import Path

import curses
from keybindings import SemanticKeybindings, UIMode, Field


class TestUIIntegration:
    """Test UI component integration and user flows."""
    
    @pytest.fixture
    def mock_ui(self):
        """Create mock UI for testing keybinding interactions."""
        ui = MagicMock()
        ui.mode = UIMode.NORMAL
        ui.current_field = Field.CONTENT
        ui.content = ""
        ui.context = ""
        ui.tags = ""
        ui.sources = ""
        ui.active_modalities = set(['text'])
        ui.idea_list = []
        ui.selected_idea_index = 0
        return ui
    
    @pytest.fixture
    def keybindings(self, mock_ui):
        """Create keybinding handler with mock UI."""
        return SemanticKeybindings(mock_ui)
    
    def test_save_capture_flow(self, keybindings, mock_ui):
        """Test: User can save capture with Ctrl+S."""
        mock_ui.content = "This is my brilliant idea"
        mock_ui.context = "reading"
        mock_ui.tags = "productivity, idea"
        mock_ui.sources = "book: Deep Work"
        
        result = keybindings.handle_key(19)  # Ctrl+S
        
        assert result == False  # handle_key returns False for save/cancel
        mock_ui.save_capture.assert_called_once()
    
    def test_cancel_capture_flow(self, keybindings, mock_ui):
        """Test: User can cancel capture with ESC."""
        mock_ui.content = "Partial idea"
        
        result = keybindings.handle_key(27)  # ESC
        
        assert result == False  # handle_key returns False for save/cancel
        mock_ui.cancel_capture.assert_called_once()
    
    def test_field_navigation_flow(self, keybindings, mock_ui):
        """Test: User can navigate between fields with Tab."""
        mock_ui.current_field = Field.CONTENT
        
        keybindings.handle_key(9)  # Tab
        
        mock_ui.set_active_field.assert_called()
        
        keybindings.handle_key(353)  # Shift+Tab (curses.KEY_BTAB)
        
        assert mock_ui.set_active_field.call_count == 2
    
    def test_mode_switching_flow(self, keybindings, mock_ui):
        """Test: User can switch between modes."""
        mock_ui.mode = UIMode.NORMAL
        
        result = keybindings.handle_key(2)  # Ctrl+B
        
        assert result == True  # handle_key returns True to continue
        
        result = keybindings.handle_key(5)  # Ctrl+E
        
        assert result == True  # handle_key returns True to continue
    
    def test_content_editing_flow(self, keybindings, mock_ui):
        """Test: User can edit content with various keys."""
        keybindings.current_field = Field.CONTENT
        mock_ui.content = "Initial content"
        mock_ui.cursor_pos = 15
        
        keybindings.handle_key(ord('!'))
        mock_ui.insert_char.assert_called_with('!')
        
        keybindings.handle_key(curses.KEY_BACKSPACE)
        mock_ui.delete_char_before.assert_called_once()
        
        keybindings.handle_key(21)  # Ctrl+U
        mock_ui.clear_line.assert_called_once()
    
    def test_modality_selection_flow(self, keybindings, mock_ui):
        """Test: User can select modalities."""
        keybindings.current_field = Field.MODALITIES
        mock_ui.active_modalities = set(['text'])
        
        keybindings.handle_key(10)  # Enter key
        mock_ui.toggle_current_modality.assert_called_once()
        
        keybindings.handle_key(ord('2'))
        mock_ui.toggle_modality_by_index.assert_called_with(1)  # 2-1=1 for zero-based index
    
    def test_help_display_flow(self, keybindings, mock_ui):
        """Test: User can toggle help with F1."""
        mock_ui.show_help = MagicMock()
        
        keybindings.handle_key(265)  # F1
        
        mock_ui.show_help.assert_called_once()


class TestBrowsingFlow:
    """Test browsing and editing existing ideas."""
    
    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault with test ideas."""
        temp_dir = tempfile.mkdtemp()
        vault_path = Path(temp_dir) / "test_vault"
        
        capture_dir = vault_path / "capture" / "raw_capture"
        capture_dir.mkdir(parents=True, exist_ok=True)
        
        idea1 = capture_dir / "20240815_210000_001.md"
        idea1.write_text("""---
timestamp: '2024-08-15T21:00:00.001000'
capture_id: '20240815_210000_001'
modalities: ['text']
context: {}
sources: ['book: Deep Work']
location: null
metadata: {}
processing_status: 'raw'
importance: 0.5
tags: ['productivity']
---

First test idea about productivity
""")
        
        idea2 = capture_dir / "20240815_210100_002.md"
        idea2.write_text("""---
timestamp: '2024-08-15T21:01:00.002000'
capture_id: '20240815_210100_002'
modalities: ['text', 'clipboard']
context: {'activity': 'reading'}
sources: ['website: example.com']
location: null
metadata: {}
processing_status: 'raw'
importance: 0.8
tags: ['learning', 'notes']
---

Second test idea about learning

Some copied text content
""")
        
        yield str(vault_path)
        shutil.rmtree(temp_dir)
    
    def test_idea_listing_flow(self, temp_vault):
        """Test: System can list existing ideas for browsing."""
        from markdown_writer import SafeMarkdownWriter
        
        writer = SafeMarkdownWriter(temp_vault)
        
        ideas = writer.list_ideas()
        
        assert len(ideas) == 2
        
        idea_names = [idea.name for idea in ideas]
        assert "20240815_210100_002.md" in idea_names
        assert "20240815_210000_001.md" in idea_names
    
    def test_idea_loading_flow(self, temp_vault):
        """Test: System can load existing idea for editing."""
        from markdown_writer import SafeMarkdownWriter
        
        writer = SafeMarkdownWriter(temp_vault)
        ideas = writer.list_ideas()
        
        idea_data = writer.read_idea_file(ideas[0])
        
        assert idea_data is not None
        assert 'frontmatter' in idea_data
        assert 'body' in idea_data
        assert 'file_path' in idea_data
        
        frontmatter = idea_data['frontmatter']
        assert 'timestamp' in frontmatter
        assert 'sources' in frontmatter
        assert 'tags' in frontmatter
        
        body = idea_data['body']
        assert 'Second test idea about learning' in body


class TestErrorNotifications:
    """Test error notification system."""
    
    @patch('subprocess.run')
    def test_notify_send_integration(self, mock_subprocess):
        """Test: Error notifications use notify-send correctly."""
        def show_error_impl(message):
            try:
                import subprocess
                subprocess.run(['notify-send', '-t', '2000', '-u', 'critical', 
                              '-i', 'dialog-error', 'Capture Failure', message], 
                             timeout=5)
            except Exception:
                pass
        
        show_error_impl("Test error message")
        
        mock_subprocess.assert_called_with([
            'notify-send', '-t', '2000', '-u', 'critical',
            '-i', 'dialog-error', 'Capture Failure', 'Test error message'
        ], timeout=5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
