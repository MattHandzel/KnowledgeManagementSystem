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
      # Using nodejs-18_x as it's a stable LTS version.
      nodejs = pkgs.nodejs-18_x;

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
      packages.kms-capture = pkgs.stdenv.mkDerivation rec {
        pname = "kms-capture";
        version = "0.1.0";

        src = self;

        nativeBuildInputs = with pkgs; [
          makeWrapper
          nodejs
          nodePackages.npm
        ];

        buildInputs = with pkgs; [
          python-env
          electron
          nodePackages.concurrently
        ];

        # We don't have a standard build phase, so we skip it
        dontBuild = true;

        installPhase = ''
          # Create the bin directory
          mkdir -p $out/bin

          # Copy the entire source code to the output path
          cp -r ${src}/* $out/

          # Install npm dependencies
          npm install --prefix $out/web
          npm install --prefix $out/electron

          # Create a wrapper script to run the application
          makeWrapper ${pkgs.nodePackages.concurrently}/bin/concurrently $out/bin/kms-capture --add-flags \
            "\"npm run dev --prefix $out/web\"" \
            "\"${python-env}/bin/python $out/server/app.py --config $out/config-dev.yaml\"" \
            "\"${pkgs.electron}/bin/electron $out/electron\""
        '';

        # Environment variable for Electron
        ELECTRON_SKIP_BINARY_DOWNLOAD = "1";
      };
    });
}
