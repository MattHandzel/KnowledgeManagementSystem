#!/usr/bin/env python3
"""
Lightweight trigger script for Hyprland keybindings.
Sends commands to the capture daemon via Unix socket.
"""

import socket
import json
import sys
import subprocess
import time
from pathlib import Path


class CaptureTrigger:
    """Handles triggering capture actions via daemon communication."""
    
    def __init__(self, socket_path: str = "/tmp/capture_daemon.sock"):
        self.socket_path = socket_path
    
    def send_command(self, action: str, mode: str = "quick", **kwargs) -> bool:
        """Send command to capture daemon."""
        command = {
            "action": action,
            "mode": mode,
            **kwargs
        }
        
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)  # 5 second timeout
                sock.connect(self.socket_path)
                sock.send(json.dumps(command).encode('utf-8'))
                
                response = sock.recv(1024).decode('utf-8')
                return response == "OK"
                
        except (ConnectionRefusedError, FileNotFoundError):
            return self.start_daemon_and_retry(command)
        except socket.timeout:
            print("Error: Daemon did not respond in time")
            return False
        except Exception as e:
            print(f"Error communicating with daemon: {e}")
            return False
    
    def start_daemon_and_retry(self, command: dict) -> bool:
        """Start the daemon and retry the command."""
        daemon_script = Path(__file__).parent / "capture_daemon.py"
        
        if not daemon_script.exists():
            print(f"Error: Daemon script not found at {daemon_script}")
            return False
        
        try:
            subprocess.Popen([
                "python3", str(daemon_script), "--daemon"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(1.0)
            
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                    sock.settimeout(5.0)
                    sock.connect(self.socket_path)
                    sock.send(json.dumps(command).encode('utf-8'))
                    
                    response = sock.recv(1024).decode('utf-8')
                    return response == "OK"
                    
            except Exception as e:
                print(f"Error: Could not connect to daemon after starting: {e}")
                return False
                
        except Exception as e:
            print(f"Error starting daemon: {e}")
            return False
    
    def quick_capture(self) -> bool:
        """Trigger quick text capture."""
        return self.send_command("show_capture", "quick")
    
    def multimodal_capture(self) -> bool:
        """Trigger multimodal capture with all options."""
        return self.send_command("show_capture", "multimodal")
    
    def voice_capture(self) -> bool:
        """Trigger voice-only capture."""
        return self.send_command("show_capture", "voice")
    
    def screenshot_capture(self) -> bool:
        """Trigger screenshot capture."""
        return self.send_command("show_capture", "screenshot")
    
    def clipboard_capture(self) -> bool:
        """Trigger clipboard capture."""
        return self.send_command("show_capture", "clipboard")
    
    def daemon_status(self) -> bool:
        """Check if daemon is running."""
        return self.send_command("status")
    
    def daemon_stop(self) -> bool:
        """Stop the daemon."""
        return self.send_command("stop")


def print_usage():
    """Print usage information."""
    print("""
Terminal Capture Daemon - Trigger Script

Usage: trigger_capture.py <command> [options]

Commands:
  quick         Quick text capture (default)
  multimodal    Full multimodal capture
  voice         Voice-only capture
  screenshot    Screenshot capture
  clipboard     Clipboard capture
  status        Check daemon status
  stop          Stop daemon

Examples:
  trigger_capture.py quick
  trigger_capture.py multimodal
  trigger_capture.py voice

This script is designed to be called from Hyprland keybindings:
  bind = SUPER, C, exec, trigger_capture.py quick
  bind = SUPER SHIFT, C, exec, trigger_capture.py multimodal
""")


def main():
    """Main entry point for trigger script."""
    if len(sys.argv) < 2:
        command = "quick"
    else:
        command = sys.argv[1].lower()
    
    if command in ["-h", "--help", "help"]:
        print_usage()
        return
    
    trigger = CaptureTrigger()
    
    success = False
    
    if command == "quick":
        success = trigger.quick_capture()
    elif command == "multimodal":
        success = trigger.multimodal_capture()
    elif command == "voice":
        success = trigger.voice_capture()
    elif command == "screenshot":
        success = trigger.screenshot_capture()
    elif command == "clipboard":
        success = trigger.clipboard_capture()
    elif command == "status":
        success = trigger.daemon_status()
        if success:
            print("Daemon is running")
        else:
            print("Daemon is not running")
    elif command == "stop":
        success = trigger.daemon_stop()
        if success:
            print("Daemon stopped")
        else:
            print("Could not stop daemon")
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)
    
    if not success and command not in ["status", "stop"]:
        print(f"Failed to execute command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
