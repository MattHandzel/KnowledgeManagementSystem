#!/usr/bin/env python3
"""
Test runner script for the capture daemon.
Runs behavioral tests and reports results.
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all tests and return success status."""
    print("🧪 Running Capture Daemon Behavioral Tests")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=project_root, capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print("\n🎯 Test Coverage Summary:")
            print("- ✅ Capture flow (text, multimodal, sources)")
            print("- ✅ File operations (atomic writes, unique names)")
            print("- ✅ UI integration (keybindings, navigation)")
            print("- ✅ Error handling (notifications, recovery)")
            print("- ✅ Configuration loading and validation")
            print("- ✅ Geolocation integration")
            print("- ✅ ISO 8601 timestamp formatting")
            return True
        else:
            print(f"\n❌ Tests failed with exit code {result.returncode}")
            return False
            
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest pytest-mock")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
