{
  description = "Knowledge Management System - Desktop Capture Application";

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

      python = pkgs.python312;
      pythonPackages = python.pkgs;

      pythonEnv = python.withPackages (ps:
        with ps; [
          fastapi
          hypercorn
          pydantic
          python-multipart
          pyyaml
        ]);

      webBuild = pkgs.buildNpmPackage {
        pname = "kms-web-build";
        version = "1.0.0";

        src = ./web;

        npmDepsHash = "sha256-1K4dpNYLOoo4DjdzWfMIRHdMbz9sRbUF4hUjQ+78VvA=";

        buildPhase = ''
          echo "=== Starting React frontend build ==="
          npm run build --verbose
          echo "=== Frontend build completed ==="
        '';

        installPhase = ''
          mkdir -p $out
          cp -r dist/* $out/
        '';
      };

      electronDeps = pkgs.buildNpmPackage {
        pname = "kms-electron-deps";
        version = "1.0.0";

        src = ./electron;

        npmDepsHash = "sha256-DPdeOcPiklVZ36xPcEdMx3yAMJdOV06A91PejTYo5D0=";

        dontBuild = true;

        npmFlags = ["--ignore-scripts"];

        installPhase = ''
          mkdir -p $out
          cp -r node_modules $out/
        '';
      };

      kms-capture = pkgs.stdenv.mkDerivation {
        pname = "kms-capture";
        version = "1.0.0";

        src = ./.;

        nativeBuildInputs = with pkgs; [
          nodejs_20
          nodePackages.npm
          makeWrapper
        ];

        buildInputs = with pkgs; [
          electron
          pythonEnv
        ];

        buildPhase = ''
          echo "=== Starting kms-capture package build ==="

          echo "Copying pre-built Electron dependencies..."
          cp -r ${electronDeps}/node_modules electron/

          echo "=== Package build phase completed ==="
        '';

        installPhase = ''
          echo "=== Starting kms-capture installation ==="
          mkdir -p $out/bin
          mkdir -p $out/lib/kms-capture

          echo "Copying Python backend server files..."
          cp -r server $out/lib/kms-capture/

          echo "Copying Python modules..."
          cp *.py $out/lib/kms-capture/

          echo "Copying built React frontend assets..."
          mkdir -p $out/lib/kms-capture/web/dist
          cp -r ${webBuild}/* $out/lib/kms-capture/web/dist/

          echo "Copying Electron application files..."
          cp -r electron $out/lib/kms-capture/

          echo "Copying configuration files..."
          cp config-prod.yaml $out/lib/kms-capture/
          cp config-dev.yaml $out/lib/kms-capture/

          echo "Creating unified wrapper script..."
          # Create wrapper script
          cat > $out/bin/kms-capture << 'EOF'
          #!/bin/bash
          set -e

          export KMS_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")/lib/kms-capture"
          export PYTHONPATH="$KMS_ROOT:$KMS_ROOT/server:$PYTHONPATH"

          # Set up writable data directory for production
          export KMS_DATA_DIR="''${KMS_DATA_DIR:-$HOME/.local/share/kms-capture}"
          mkdir -p "$KMS_DATA_DIR"

          cd "$KMS_ROOT"

          # Start backend server in background
          python server/app.py --config config-prod.yaml &
          SERVER_PID=$!

          # Function to cleanup processes
          cleanup() {
            echo "Cleaning up processes..."
            kill $SERVER_PID 2>/dev/null || true
            exit 0
          }

          # Set up signal handlers
          trap cleanup SIGINT SIGTERM EXIT

          # Start Electron app
          cd electron
          electron . --no-sandbox

          # Cleanup will be called by trap
          EOF

          echo "Making wrapper script executable and setting up PATH..."
          # Make the wrapper script executable and wrap it with proper paths
          chmod +x $out/bin/kms-capture
          wrapProgram $out/bin/kms-capture \
            --prefix PATH : ${pkgs.lib.makeBinPath [pythonEnv pkgs.electron pkgs.nodejs_20]}


          # Create desktop entry
          mkdir -p $out/share/applications
          cat > $out/share/applications/kms-capture.desktop << EOF
          [Desktop Entry]
          Name=Knowledge Management System
          Comment=Desktop capture application for knowledge management
          Exec=$out/bin/kms-capture
          Icon=kms-capture
          Terminal=false
          Type=Application
          Categories=Office;Utility;
          EOF

          echo "=== kms-capture installation completed successfully ==="
        '';

        meta = with pkgs.lib; {
          description = "Knowledge Management System - Desktop Capture Application";
          homepage = "https://github.com/MattHandzel/KnowledgeManagementSystem";
          license = licenses.mit;
          platforms = platforms.linux;
          maintainers = [];
        };
      };
    in {
      packages = {
        default = kms-capture;
        kms-capture = kms-capture;
        webBuild = webBuild;
        electronDeps = electronDeps;
      };

      apps = {
        default = {
          type = "app";
          program = "${kms-capture}/bin/kms-capture";
        };
      };

      devShells.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          nodejs_20
          nodePackages.npm
          pythonEnv
          electron
        ];

        shellHook = ''
          echo "Knowledge Management System Development Environment"
          echo "Available commands:"
          echo "  cd server && python app.py          # Start backend server"
          echo "  cd web && npm run dev               # Start frontend dev server"
          echo "  cd electron && npm start            # Start Electron app"
          echo "  nix build                           # Build the package"
          echo "  nix run .#                          # Run the desktop app"
        '';
      };
    });
}
