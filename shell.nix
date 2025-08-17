{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Core dependencies
    python3
    python3Packages.pyyaml
    python3Packages.watchdog
    python3Packages.fastapi
    python3Packages.uvicorn
    python3Packages.python-multipart
    
    
    # Capture tools
    grim          # Screenshots
    slurp         # Screen selection
    wl-clipboard  # Clipboard access
    wf-recorder   # Screen recording
    alsa-utils    # Audio recording (arecord)
    curl          # Geolocation API calls
    libnotify     # notify-send for error notifications
    
    # Node.js and Electron dependencies
    nodejs
    yarn
    npm
    
    # Electron system libraries
    xorg.libX11
    xorg.libXext
    xorg.libXrandr
    xorg.libXrender
    xorg.libXtst
    xorg.libXScrnSaver
    xorg.libxkbfile
    xorg.libXi
    gtk3
    glib
    nss
    nspr
    atk
    at-spi2-atk
    cups
    drm
    gtk3
    libxkbcommon
    mesa
    expat
    libxshmfence
    alsa-lib
    at-spi2-core
    dbus
    
    # Development tools
    python3Packages.pytest
    python3Packages.black
    python3Packages.flake8
    python3Packages.mypy
  ];
  
  shellHook = ''
    echo "🚀 Knowledge Management System Development Environment"
    echo ""
    echo "Available commands:"
    echo "  # Web application:"
    echo "  cd server && python app.py           # Start backend"
    echo "  cd web && npm run dev                # Start frontend"
    echo ""
    echo "  # Electron desktop app:"
    echo "  cd electron && npm install           # Install deps"
    echo "  cd electron && npm run dev           # Launch desktop app"
    echo ""
    echo "  # Testing:"
    echo "  pytest tests/                        # Run tests"
    echo "  black *.py                           # Format code"
    echo "  flake8 *.py                          # Lint code"
    echo ""
    
    # Create required directories
    mkdir -p ~/notes/capture/raw_capture/media
    
    
    # Make scripts executable
    chmod +x *.py
    
    # Set up environment variables for Electron
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
      pkgs.xorg.libX11
      pkgs.xorg.libXext
      pkgs.xorg.libXrandr
      pkgs.xorg.libXrender
      pkgs.xorg.libXtst
      pkgs.xorg.libXScrnSaver
      pkgs.xorg.libxkbfile
      pkgs.xorg.libXi
      pkgs.gtk3
      pkgs.glib
      pkgs.nss
      pkgs.nspr
      pkgs.atk
      pkgs.at-spi2-atk
      pkgs.cups
      pkgs.drm
      pkgs.libxkbcommon
      pkgs.mesa
      pkgs.expat
      pkgs.libxshmfence
      pkgs.alsa-lib
      pkgs.at-spi2-core
      pkgs.dbus
    ]}:$LD_LIBRARY_PATH"
    
    # Electron sandboxing fixes
    export ELECTRON_DISABLE_SANDBOX=1
    export ELECTRON_RUN_AS_NODE=0
  '';
}
