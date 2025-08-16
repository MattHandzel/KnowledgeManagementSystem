{pkgs ? import <nixpkgs> {}}: let
  # Common Electron dependencies
  electronDeps = with pkgs; [
    # Core system libraries
    glib
    gtk3
    libgbm # For hardware-accelerated rendering
    libglvnd # Vendor-neutral dispatch layer for GL implementations
    nss
    nspr # Provides libnspr4.so
    at-spi2-core
    at-spi2-atk
    atk
    c-ares
    cairo
    cups
    dbus
    expat
    gdk-pixbuf
    gtk2
    gtk3
    libxkbcommon
    # libxshmfence
    pango
    xorg.libX11
    xorg.libxcb
    xorg.libXcomposite
    xorg.libXcursor
    xorg.libXdamage
    xorg.libXext
    xorg.libXfixes
    xorg.libXi
    xorg.libXrandr
    xorg.libXrender
    xorg.libXScrnSaver
    xorg.libXtst
    xorg.libxshmfence
    xorg.libxkbfile
    xorg.libXxf86vm
    xorg.libXinerama
    xorg.libXv
    xorg.xcbutil
    xorg.xcbutilwm
    xorg.xcbutilimage
    xorg.xcbutilkeysyms
    xorg.xcbutilrenderutil
    xorg.xcbutilcursor
    xorg.xcbutil
    xorg.libXrandr
    xorg.libXScrnSaver
    xorg.libXcursor
    xorg.libXdamage
    xorg.libXcomposite
    xorg.libXext
    xorg.libXfixes
    xorg.libXi
    xorg.libXrender
    xorg.libX11
    xorg.libxcb
    libdrm
    mesa
    alsa-lib
    libcap
    libnotify
    libpng
    libtool
    libxkbcommon
    # libxkbfile
    # libxshmfence
    nspr
    nss
    pciutils
    pango
    pciutils
    systemd
    xdg-utils
  ];
in
  pkgs.mkShell {
    buildInputs = with pkgs;
      [
        # Node.js development
        nodejs
        yarn
        nodePackages.npm
        nodePackages.pnpm

        # Python development (for backend)
        python311
        python311Packages.pip
        python311Packages.virtualenv

        # Development tools
        git
        gcc
        gnumake
        pkg-config
      ]
      ++ electronDeps;

    # Set environment variables
    shellHook = ''
      # Set library path for Electron
      export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath electronDeps}:$LD_LIBRARY_PATH

      echo "Environment ready! Run 'npm run dev' to start the development server."
    '';

    # Fix for Electron sandboxing
    ELECTRON_RUN_AS_NODE = "1";
    ELECTRON_FORCE_WINDOW_MENU_BAR = "1";
    NIX_CFLAGS_COMPILE = "-I${pkgs.alsa-lib.dev}/include/alsa";
  }
