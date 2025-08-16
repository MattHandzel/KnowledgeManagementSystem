#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_capture_data():
    """Return sample capture data for testing."""
    from datetime import datetime
    
    return {
        'timestamp': datetime(2024, 8, 15, 21, 30, 45, 123456),
        'content': 'This is a test capture idea',
        'context': {'activity': 'testing'},
        'tags': ['test', 'development'],
        'sources': ['manual: test case'],
        'modalities': ['text'],
    }
