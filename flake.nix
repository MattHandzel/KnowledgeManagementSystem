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
        program = let
          script = pkgs.writeShellScriptBin "run-kms-capture" ''
            set -e
            # Ensure node_modules are installed before running
            if [ ! -d "web/node_modules" ]; then
                echo "'web/node_modules' not found. Running 'npm install' in 'web' directory..."
                npm install --prefix web
            fi
            if [ ! -d "electron/node_modules" ]; then
                echo "'electron/node_modules' not found. Running 'npm install' in 'electron' directory..."
                npm install --prefix electron
            fi

            echo "Starting application..."
            ${pkgs.nodePackages.concurrently}/bin/concurrently \
              "npm run dev --prefix ./web" \
              "${python-env}/bin/python ./server/app.py --config ./config-prod.yaml" \
              "${pkgs.electron}/bin/electron ./electron"
          '';
        in
          "${script}/bin/run-kms-capture";
      };
    });
}
