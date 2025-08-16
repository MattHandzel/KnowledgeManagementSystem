#!/usr/bin/env python3
"""
Geolocation functionality using IP-based lookup.
Provides device location data for capture metadata.
"""

import subprocess
import json
from typing import Optional, Dict, Any


def get_device_location(timeout: float = 1.0) -> Optional[Dict[str, Any]]:
    """Get device location using IP-based geolocation."""
    try:
        result = subprocess.run(['curl', '-s', 'http://ip-api.com/json/'],
                              capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('status') == 'success':
                return {
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                    'city': data.get('city'),
                    'country': data.get('country'),
                    'timezone': data.get('timezone')
                }
    except Exception as e:
        print(f"Geolocation failed: {e}")
    return None


if __name__ == "__main__":
    location = get_device_location()
    if location:
        print(f"Location: {location}")
    else:
        print("Failed to get location")
