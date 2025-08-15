#!/usr/bin/env python3
"""Test script to verify all imports work correctly."""

import sys
sys.path.append('.')

try:
    from capture_daemon import CaptureUI
    from keybindings import UIMode, Field
    from markdown_writer import SafeMarkdownWriter
    from geolocation import get_device_location
    
    print('✓ All imports successful')
    print('✓ UIMode enum:', list(UIMode))
    print('✓ Field enum:', list(Field))
    print('✓ Testing geolocation...')
    
    location = get_device_location()
    if location:
        print(f'✓ Geolocation works: {location["city"]}, {location["country"]}')
    else:
        print('⚠ Geolocation failed (expected in some environments)')
    
    print('✓ Testing markdown writer...')
    writer = SafeMarkdownWriter("~/notes")
    print(f'✓ Markdown writer initialized with vault: {writer.vault_path}')
    
    print('\n✅ All tests passed!')
    
except Exception as e:
    print(f'❌ Import test failed: {e}')
    sys.exit(1)
