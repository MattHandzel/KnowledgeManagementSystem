{
  description = "Knowledge Management System";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true; # Required for some packages
      };

      # 1. Python Backend Dependencies
      python-env = pkgs.python311.withPackages (ps: with ps; [
        fastapi
        hypercorn
        pydantic
        python-multipart
        pyyaml
        sounddevice
        numpy
        websockets
      ]);

      # 2. Frontend and Electron Dependencies
      # Using nodejs-20_x as it's a stable LTS version.
      nodejs = pkgs.nodejs_22;

    in {

      # 3. Development Shell
      # You can enter this shell by running `nix develop`
      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [
          # Python environment
          python-env

          # Node.js environment
          nodejs
          # For running scripts concurrently
          nodePackages.concurrently

          # Electron from nixpkgs
          electron

          # System libraries from shell.nix
          zlib
          portaudio
        ];

        # Environment variable to prevent Electron from downloading binaries
        shellHook = ''
          export ELECTRON_SKIP_BINARY_DOWNLOAD=1
          # Advise user on next steps
          echo "Welcome to the development environment!"
          echo "First, run 'npm install' in the 'web' and 'electron' directories."
          echo "Then, you can start the application with 'nix run'."
        '';
      };

      # 4. Runnable App
      # You can run this with `nix run .#kms-capture`
      apps.kms-capture = {
        type = "app";
        program = "${self.packages.${system}.kms-capture}/bin/kms-capture";
      };

      # 5. Buildable Package
      # You can build this with `nix build .#kms-capture`
      packages.kms-capture = let
        # Helper function to build node modules
        buildNodeModules = { pname, src, npmDepsHash }: pkgs.buildNpmPackage {
          inherit pname src npmDepsHash;
          version = "0.1.0";
          dontNpmBuild = true;
          
          # Prevents electron from downloading binaries during build
          env.ELECTRON_SKIP_BINARY_DOWNLOAD = "1";
        };

        # Build node_modules for web and electron separately
        webModules = buildNodeModules {
          pname = "kms-web";
          src = ./web;
          npmDepsHash = "sha256-nGYsAkFt8njX9FalvcY/8CQAXLIGt6rxhUxxULPKjiE=";
        };

        electronModules = buildNodeModules {
          pname = "kms-electron";
          src = ./electron;
          npmDepsHash = "sha256-DPdeOcPiklVZ36xPcEdMx3yAMJdOV06A91PejTYo5D0=";
        };
      in
        pkgs.stdenv.mkDerivation rec {
          pname = "kms-capture";
          version = "0.1.0";

          src = ./.;

          nativeBuildInputs = with pkgs; [
            makeWrapper
          ];

          # We don't have a standard build phase, so we skip it
          dontBuild = true;

          installPhase = ''
            mkdir -p $out/bin
            cp -r ${src}/* $out/

            # Make the destination writable
            chmod -R u+w $out

            # Link the pre-built node_modules
            ln -s ${webModules}/lib/node_modules $out/web/node_modules
            ln -s ${electronModules}/lib/node_modules $out/electron/node_modules

            # Create a helper script to run the application
            cat > $out/bin/run-kms <<'EOF'
            #!/bin/sh
            # Change to the package's directory before running
            cd $out
            ${pkgs.nodePackages.concurrently}/bin/concurrently \
              "npm run dev --prefix ~/Projects/KnowledgeManagementSystem/web" \
              "${python-env}/bin/python ~/Projects/KnowledgeManagementSystem/server/app.py --config ./config-prod.yaml" \
              "${pkgs.electron}/bin/electron ~/Projects/KnowledgeManagementSystem/electron"
            EOF
            chmod +x $out/bin/run-kms

            # Wrap the helper script
            makeWrapper $out/bin/run-kms $out/bin/kms-capture
          '';
        };
    });
}
