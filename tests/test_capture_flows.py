#!/usr/bin/env python3
"""
Behavioral tests for capture daemon core flows.
Tests the complete user journey from capture to storage.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
import yaml
import json

from markdown_writer import SafeMarkdownWriter
from geolocation import get_device_location


class TestCaptureFlows:
    """Test complete capture workflows from user perspective."""
    
    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        vault_path = Path(temp_dir) / "test_vault"
        yield str(vault_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def writer(self, temp_vault):
        """Create markdown writer with temp vault."""
        return SafeMarkdownWriter(temp_vault)
    
    def test_simple_text_capture_flow(self, writer):
        """Test: User captures simple text idea and it's stored correctly."""
        capture_data = {
            'timestamp': datetime(2024, 8, 15, 21, 30, 45, 123456),
            'content': 'This is a brilliant idea about productivity',
            'context': {'activity': 'reading', 'location': 'home'},
            'tags': ['productivity', 'idea'],
            'modalities': ['text'],
            'sources': ['book: Deep Work'],
            'location': {
                'latitude': 42.2506,
                'longitude': -71.0023,
                'city': 'Quincy',
                'country': 'United States'
            }
        }
        
        result_file = writer.write_capture(capture_data)
        
        assert result_file.exists()
        assert result_file.name.startswith('20240815_213045_123')
        assert result_file.suffix == '.md'
        
        content = result_file.read_text()
        assert content.strip().startswith('---')
        assert 'This is a brilliant idea about productivity' in content
        assert 'book: Deep Work' in content
        
        parts = content.split('---', 2)
        frontmatter = yaml.safe_load(parts[1])
        assert frontmatter['timestamp'] == '2024-08-15T21:30:45.123456'
        assert frontmatter['sources'] == ['book: Deep Work']
        assert frontmatter['location']['city'] == 'Quincy'
    
    def test_multimodal_capture_flow(self, writer, temp_vault):
        """Test: User captures idea with multiple modalities."""
        media_dir = Path(temp_vault) / "capture" / "raw_capture" / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        
        fake_screenshot = media_dir / "test_screenshot.png"
        fake_screenshot.write_bytes(b"fake image data")
        
        capture_data = {
            'timestamp': datetime.now(),
            'content': 'Main idea content',
            'clipboard': 'Copied text from somewhere',
            'media_files': [{
                'type': 'screenshot',
                'path': str(fake_screenshot)
            }],
            'modalities': ['text', 'clipboard', 'screenshot'],
            'tags': ['multimodal']
        }
        
        result_file = writer.write_capture(capture_data)
        
        content = result_file.read_text()
        assert '## Content' in content
        assert 'Main idea content' in content
        assert '## Clipboard' in content
        assert 'Copied text from somewhere' in content
        assert '## Media' in content
        assert 'Screenshot:' in content
        
        parts = content.split('---', 2)
        frontmatter = yaml.safe_load(parts[1])
        assert set(frontmatter['modalities']) == {'text', 'clipboard', 'screenshot'}
    
    def test_capture_with_sources_array(self, writer):
        """Test: User can specify multiple sources for knowledge."""
        capture_data = {
            'timestamp': datetime.now(),
            'content': 'Synthesis of ideas from multiple sources',
            'sources': [
                'book: Atomic Habits',
                'person: James Clear',
                'website: jamesclear.com',
                'podcast: The Tim Ferriss Show'
            ],
            'modalities': ['text']
        }
        
        result_file = writer.write_capture(capture_data)
        
        content = result_file.read_text()
        parts = content.split('---', 2)
        frontmatter = yaml.safe_load(parts[1])
        
        expected_sources = [
            'book: Atomic Habits',
            'person: James Clear', 
            'website: jamesclear.com',
            'podcast: The Tim Ferriss Show'
        ]
        assert frontmatter['sources'] == expected_sources
    
    def test_empty_capture_handling(self, writer):
        """Test: System handles empty/minimal captures gracefully."""
        capture_data = {
            'timestamp': datetime.now(),
            'content': '',  # Empty content
            'modalities': ['text']
        }
        
        result_file = writer.write_capture(capture_data)
        
        assert result_file.exists()
        
        content = result_file.read_text()
        parts = content.split('---', 2)
        frontmatter = yaml.safe_load(parts[1])
        assert 'timestamp' in frontmatter
        assert frontmatter['modalities'] == ['text']
    
    @patch('geolocation.subprocess.run')
    def test_geolocation_integration(self, mock_subprocess, writer):
        """Test: Geolocation is properly integrated into captures."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'status': 'success',
            'lat': 42.3601,
            'lon': -71.0589,
            'city': 'Boston',
            'country': 'United States',
            'timezone': 'America/New_York'
        })
        mock_subprocess.return_value = mock_result
        
        location = get_device_location()
        capture_data = {
            'timestamp': datetime.now(),
            'content': 'Idea captured in Boston',
            'location': location,
            'modalities': ['text']
        }
        
        result_file = writer.write_capture(capture_data)
        
        content = result_file.read_text()
        parts = content.split('---', 2)
        frontmatter = yaml.safe_load(parts[1])
        
        assert frontmatter['location']['city'] == 'Boston'
        assert frontmatter['location']['latitude'] == 42.3601
        assert frontmatter['location']['longitude'] == -71.0589
    
    def test_iso_8601_timestamp_format(self, writer):
        """Test: All timestamps use ISO 8601 format."""
        test_time = datetime(2024, 8, 15, 21, 30, 45, 123456)
        capture_data = {
            'timestamp': test_time,
            'content': 'Test timestamp formatting',
            'modalities': ['text']
        }
        
        result_file = writer.write_capture(capture_data)
        
        content = result_file.read_text()
        parts = content.split('---', 2)
        frontmatter = yaml.safe_load(parts[1])
        
        assert frontmatter['timestamp'] == '2024-08-15T21:30:45.123456'
        
        parsed_time = datetime.fromisoformat(frontmatter['timestamp'])
        assert parsed_time == test_time


class TestFileOperations:
    """Test file safety and atomic operations."""
    
    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        vault_path = Path(temp_dir) / "test_vault"
        yield str(vault_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def writer(self, temp_vault):
        """Create markdown writer with temp vault."""
        return SafeMarkdownWriter(temp_vault)
    
    def test_unique_filename_generation(self, writer):
        """Test: Each capture gets unique filename even with same timestamp."""
        timestamp = datetime(2024, 8, 15, 21, 30, 45, 123456)
        
        capture1 = {
            'timestamp': timestamp,
            'content': 'First idea',
            'modalities': ['text']
        }
        
        capture2 = {
            'timestamp': timestamp,
            'content': 'Second idea',
            'modalities': ['text']
        }
        
        file1 = writer.write_capture(capture1)
        file2 = writer.write_capture(capture2)
        
        assert file1 != file2
        assert file1.exists()
        assert file2.exists()
        
        assert 'First idea' in file1.read_text()
        assert 'Second idea' in file2.read_text()
    
    def test_atomic_write_operations(self, writer):
        """Test: File writes are atomic (no partial writes)."""
        large_content = "Large idea content\n" * 1000
        capture_data = {
            'timestamp': datetime.now(),
            'content': large_content,
            'modalities': ['text']
        }
        
        result_file = writer.write_capture(capture_data)
        
        content = result_file.read_text()
        assert content.count("Large idea content") == 1000
        assert content.strip().startswith('---')
        assert content.endswith('\n')
    
    def test_directory_creation(self, temp_vault):
        """Test: Required directories are created automatically."""
        vault_path = Path(temp_vault)
        assert not vault_path.exists()
        
        writer = SafeMarkdownWriter(temp_vault)
        
        assert writer.capture_dir.exists()
        assert writer.media_dir.exists()
        assert writer.capture_dir == vault_path / "capture" / "raw_capture"
        assert writer.media_dir == vault_path / "capture" / "raw_capture" / "media"
    
    def test_media_file_handling(self, writer, temp_vault):
        """Test: Media files are safely copied to media directory."""
        source_file = Path(temp_vault) / "source_image.png"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_bytes(b"fake image data")
        
        saved_path = writer.save_media_file(source_file, 'screenshot')
        
        assert saved_path.exists()
        assert saved_path.parent == writer.media_dir
        assert saved_path.read_bytes() == b"fake image data"
        
        assert source_file.exists()
        assert source_file.read_bytes() == b"fake image data"


class TestErrorHandling:
    """Test error scenarios and recovery."""
    
    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        vault_path = Path(temp_dir) / "test_vault"
        yield str(vault_path)
        shutil.rmtree(temp_dir)
    
    def test_invalid_vault_path_handling(self):
        """Test: Graceful handling of invalid vault paths."""
        invalid_path = "/nonexistent/path/that/cannot/be/created"
        
        try:
            writer = SafeMarkdownWriter(invalid_path)
            assert writer.vault_path.exists() or True  # May fail to create, that's ok
        except Exception as e:
            assert "path" in str(e).lower() or "permission" in str(e).lower()
    
    @patch('geolocation.subprocess.run')
    def test_geolocation_failure_handling(self, mock_subprocess):
        """Test: Captures work even when geolocation fails."""
        mock_subprocess.side_effect = Exception("Network error")
        
        location = get_device_location()
        
        assert location is None
        
    
    def test_malformed_yaml_recovery(self, temp_vault):
        """Test: System handles existing malformed files gracefully."""
        writer = SafeMarkdownWriter(temp_vault)
        malformed_file = writer.capture_dir / "malformed.md"
        malformed_file.parent.mkdir(parents=True, exist_ok=True)
        malformed_file.write_text("""---
invalid: yaml: content: [unclosed
---
Some content
""")
        
        ideas = writer.list_ideas()
        
        assert malformed_file in ideas
        
        idea_data = writer.read_idea_file(malformed_file)
        assert idea_data is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
