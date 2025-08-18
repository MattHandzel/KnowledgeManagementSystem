{
  description = "Knowledge Management System - Desktop Capture Application";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        python = pkgs.python312;
        pythonPackages = python.pkgs;
        
        pythonEnv = python.withPackages (ps: with ps; [
          fastapi
          hypercorn
          pydantic
          python-multipart
          pyyaml
        ]);

        webBuild = pkgs.stdenv.mkDerivation {
          pname = "kms-web-build";
          version = "1.0.0";
          
          src = ./web;
          
          nativeBuildInputs = with pkgs; [
            nodejs_20
            nodePackages.npm
          ];
          
          buildPhase = ''
            export HOME=$TMPDIR
            export npm_config_cache=$TMPDIR/.npm
            npm ci
            npm run build
          '';
          
          installPhase = ''
            mkdir -p $out
            cp -r dist/* $out/
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
            export HOME=$TMPDIR
            export npm_config_cache=$TMPDIR/.npm
            
            # Install electron dependencies
            cd electron
            npm ci
            cd ..
          '';
          
          installPhase = ''
            mkdir -p $out/bin
            mkdir -p $out/lib/kms-capture
            
            # Copy server files
            cp -r server $out/lib/kms-capture/
            
            # Copy built web assets
            mkdir -p $out/lib/kms-capture/web/dist
            cp -r ${webBuild}/* $out/lib/kms-capture/web/dist/
            
            # Copy electron files and node_modules
            cp -r electron $out/lib/kms-capture/
            
            # Copy configuration files
            cp config-prod.yaml $out/lib/kms-capture/
            cp config-dev.yaml $out/lib/kms-capture/
            
            # Create wrapper script
            cat > $out/bin/kms-capture << 'EOF'
            #!/bin/bash
            set -e
            
            export KMS_ROOT="$out/lib/kms-capture"
            export PYTHONPATH="$KMS_ROOT/server:$PYTHONPATH"
            
            cd "$KMS_ROOT"
            
            # Start backend server in background
            python server/app.py --config config-prod.yaml &
            SERVER_PID=$!
            
            # Wait for server to start
            sleep 3
            
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
            
            # Make the wrapper script executable and wrap it with proper paths
            chmod +x $out/bin/kms-capture
            wrapProgram $out/bin/kms-capture \
              --prefix PATH : ${pkgs.lib.makeBinPath [ pythonEnv pkgs.electron pkgs.nodejs_20 ]}
            
            
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
          '';
          
          meta = with pkgs.lib; {
            description = "Knowledge Management System - Desktop Capture Application";
            homepage = "https://github.com/MattHandzel/KnowledgeManagementSystem";
            license = licenses.mit;
            platforms = platforms.linux;
            maintainers = [ ];
          };
        };

      in
      {
        packages = {
          default = kms-capture;
          kms-capture = kms-capture;
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
