{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Core dependencies
    python3
    python3Packages.pyyaml
    python3Packages.watchdog
    
    # Terminal UI
    ncurses
    
    # Capture tools
    grim          # Screenshots
    slurp         # Screen selection
    wl-clipboard  # Clipboard access
    wf-recorder   # Screen recording
    alsa-utils    # Audio recording (arecord)
    curl          # Geolocation API calls
    libnotify     # notify-send for error notifications
    
    # Development tools
    python3Packages.pytest
    python3Packages.black
    python3Packages.flake8
    python3Packages.mypy
  ];
  
  shellHook = ''
    echo "🚀 Terminal Capture Daemon Development Environment"
    echo ""
    echo "Available commands:"
    echo "  python capture_daemon.py --daemon    # Start daemon"
    echo "  python trigger_capture.py quick      # Test trigger"
    echo "  pytest tests/                        # Run tests"
    echo "  black *.py                           # Format code"
    echo "  flake8 *.py                          # Lint code"
    echo ""
    echo "Hyprland keybind examples:"
    echo "  bind = SUPER, C, exec, python $(pwd)/trigger_capture.py quick"
    echo "  bind = SUPER SHIFT, C, exec, python $(pwd)/trigger_capture.py multimodal"
    echo ""
    
    # Create required directories
    mkdir -p ~/notes/capture/raw_capture/media
    
    # Set up socket directory
    mkdir -p /tmp/capture_daemon
    
    # Make scripts executable
    chmod +x *.py
    
    export PYTHONPATH="$(pwd):$PYTHONPATH"
  '';
}
