#!/usr/bin/env python3
"""
Tests for configuration loading and validation.
"""

import pytest
import tempfile
import yaml
from pathlib import Path



class TestConfigurationLoading:
    """Test configuration file loading and validation."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for config files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_default_config_loading(self, temp_config_dir):
        """Test: Default configuration loads correctly."""
        config_file = temp_config_dir / "config.yaml"
        default_config = {
            'vault': {
                'path': '~/notes',
                'capture_dir': 'capture/raw_capture',
                'media_dir': 'capture/raw_capture/media'
            },
            'daemon': {
                'socket_path': '/tmp/capture_daemon.sock',
                'auto_start': True
            },
            'capture': {
                'geolocation_enabled': True,
                'sources_suggestions': True
            }
        }
        
        with config_file.open('w') as f:
            yaml.dump(default_config, f)
        
        loader = ConfigLoader(str(config_file))
        config = loader.load()
        
        assert 'vault' in config
        assert 'daemon' in config
        assert 'capture' in config
        
        assert config['vault']['path'] == '~/notes'
        assert config['daemon']['auto_start'] is True
        assert config['capture']['geolocation_enabled'] is True
    
    def test_config_validation(self, temp_config_dir):
        """Test: Invalid configuration is caught."""
        config_file = temp_config_dir / "invalid_config.yaml"
        invalid_config = {
            'vault': {
                'path': None  # Invalid: path cannot be None
            },
            'daemon': {
                'socket_path': ''  # Invalid: empty socket path
            }
        }
        
        with config_file.open('w') as f:
            yaml.dump(invalid_config, f)
        
        loader = ConfigLoader(str(config_file))
        with pytest.raises(ValueError, match="Invalid configuration"):
            loader.load()
    
    def test_missing_config_file(self):
        """Test: Missing config file uses defaults."""
        loader = ConfigLoader("/nonexistent/config.yaml")
        
        config = loader.load()
        
        assert config['vault']['path'] == '~/notes'
        assert config['daemon']['socket_path'] == '/tmp/capture_daemon.sock'


class ConfigLoader:
    """Simple configuration loader for testing."""
    
    def __init__(self, config_path):
        self.config_path = Path(config_path)
    
    def load(self):
        """Load configuration from file or return defaults."""
        if not self.config_path.exists():
            return self._get_defaults()
        
        try:
            with self.config_path.open() as f:
                config = yaml.safe_load(f)
            
            self._validate_config(config)
            return config
            
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}")
    
    def _get_defaults(self):
        """Return default configuration."""
        return {
            'vault': {
                'path': '~/notes',
                'capture_dir': 'capture/raw_capture',
                'media_dir': 'capture/raw_capture/media'
            },
            'daemon': {
                'socket_path': '/tmp/capture_daemon.sock',
                'auto_start': True
            },
            'capture': {
                'geolocation_enabled': True,
                'sources_suggestions': True
            }
        }
    
    def _validate_config(self, config):
        """Validate configuration structure."""
        if not config.get('vault', {}).get('path'):
            raise ValueError("Vault path is required")
        
        if not config.get('daemon', {}).get('socket_path'):
            raise ValueError("Socket path is required")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
