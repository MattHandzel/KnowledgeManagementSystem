{
  description = "Knowledge Management System - Electron Desktop App";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};

      # Build the React frontend
      web-frontend = pkgs.buildNpmPackage {
        pname = "kms-web-frontend";
        version = "0.1.0";

        src = ./web;

        npmDepsHash = "sha256-2W1PTK281uXTKTXcjC4Swt367WTHp7g3ehdJt8nqCRA=";

        buildPhase = ''
          npm run build
        '';

        installPhase = ''
          mkdir -p $out
          cp -r dist/* $out/
        '';
      };

      # Main Electron application
      kms-electron = pkgs.stdenv.mkDerivation {
        pname = "knowledge-management-system-capture";
        version = "1.0.0";

        src = ./.;

        nativeBuildInputs = with pkgs; [
          python3
          python3Packages.pip
          python3Packages.setuptools
          makeWrapper
        ];

        buildInputs = with pkgs; [
          # Python backend dependencies
          python3Packages.fastapi
          python3Packages.hypercorn
          python3Packages.pyyaml
          python3Packages.python-multipart
          python3Packages.typing-extensions

          # Use Nix's pre-built Electron
          electron

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
          libdrm
          libxkbcommon
          mesa
          expat
          xorg.libxshmfence
          alsa-lib
          at-spi2-core
          dbus

          # Capture tools for functionality
          grim
          slurp
          wl-clipboard
          wf-recorder
          alsa-utils
        ];

        buildPhase = ''
          # No build phase needed - we'll copy files directly
        '';

        installPhase = ''
          mkdir -p $out/bin
          mkdir -p $out/lib/kms-electron

          # Copy electron app files (main.js, package.json)
          cp -r electron $out/lib/kms-electron/

          # Copy server backend
          cp -r server $out/lib/kms-electron/

          # Copy built web frontend
          mkdir -p $out/lib/kms-electron/web
          cp -r ${web-frontend} $out/lib/kms-electron/web/dist

          # Copy config
          cp config.yaml $out/lib/kms-electron/

          # Create wrapper script that uses Nix's Electron
          makeWrapper ${pkgs.electron}/bin/electron $out/bin/kms-electron \
            --chdir $out/lib/kms-electron/electron \
            --set ELECTRON_DISABLE_SANDBOX 1 \
            --prefix PYTHONPATH : "$out/lib/kms-electron/server:$out/lib/kms-electron" \
            --prefix LD_LIBRARY_PATH : "${pkgs.lib.makeLibraryPath [
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
            pkgs.libdrm
            pkgs.libxkbcommon
            pkgs.mesa
            pkgs.expat
            pkgs.xorg.libxshmfence
            pkgs.alsa-lib
            pkgs.at-spi2-core
            pkgs.dbus
          ]}" \
            --add-flags "."
        '';

        meta = with pkgs.lib; {
          description = "Knowledge Management System - Capture";
          homepage = "https://github.com/MattHandzel/KnowledgeManagementSystem";
          license = licenses.mit;
          maintainers = ["MattHandzel"];
          platforms = platforms.linux;
        };
      };
    in {
      # Development shell (keep existing shell.nix functionality)
      devShells.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          # Core dependencies
          python3
          python3Packages.fastapi
          python3Packages.hypercorn
          python3Packages.pyyaml
          python3Packages.python-multipart
          python3Packages.typing-extensions

          # Node.js and Electron dependencies
          nodejs
          yarn
          nodePackages.npm

          # Electron system libraries (from shell.nix)
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
          libdrm
          libxkbcommon
          mesa
          expat
          xorg.libxshmfence
          alsa-lib
          at-spi2-core
          dbus

          # Capture tools
          grim
          slurp
          wl-clipboard
          wf-recorder
          alsa-utils

          # Development tools
          python3Packages.pytest
          python3Packages.black
          python3Packages.flake8
          python3Packages.mypy
          nixpkgs-fmt
        ];

        shellHook = ''
          echo "🚀 Knowledge Management System - Electron Development Environment"
          echo ""
          echo "Available commands:"
          echo "  cd server && python app.py           # Start backend"
          echo "  cd web && npm run dev                # Start frontend"
          echo "  cd electron && npm install && npm start  # Launch Electron app"
          echo ""
          echo "Build commands:"
          echo "  nix build                            # Build Electron package"
          echo "  nix run                              # Run built Electron app"
          echo ""

          # Create required directories
          mkdir -p ~/notes/capture/raw_capture/media

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
            pkgs.libdrm
            pkgs.libxkbcommon
            pkgs.mesa
            pkgs.expat
            pkgs.xorg.libxshmfence
            pkgs.alsa-lib
            pkgs.at-spi2-core
            pkgs.dbus
          ]}:$LD_LIBRARY_PATH"

          # Electron sandboxing fixes
          export ELECTRON_DISABLE_SANDBOX=1
          export ELECTRON_RUN_AS_NODE=0
        '';
      };

      # Package outputs
      packages = {
        default = kms-electron;
        kms-electron = kms-electron;
        web-frontend = web-frontend;
      };

      # App for easy running
      apps = {
        default = {
          type = "app";
          program = "${kms-electron}/bin/kms-electron";
        };
      };

      # NixOS module for system integration
      nixosModules.kms-electron = {
        config,
        lib,
        pkgs,
        ...
      }:
        with lib; let
          cfg = config.services.kms-electron;
        in {
          options.services.kms-electron = {
            enable = mkEnableOption "Knowledge Management System Electron App";

            user = mkOption {
              type = types.str;
              default = "user";
              description = "User to install the app for";
            };

            vaultPath = mkOption {
              type = types.str;
              default = "/home/${cfg.user}/notes";
              description = "Path to the notes vault";
            };
          };

          config = mkIf cfg.enable {
            environment.systemPackages = [kms-electron];

            # Ensure required directories exist
            systemd.tmpfiles.rules = [
              "d ${cfg.vaultPath}/capture/raw_capture/media 0755 ${cfg.user} users -"
            ];
          };
        };
    });
}
