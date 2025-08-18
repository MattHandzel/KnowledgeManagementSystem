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

      # Main Electron application
      kms-electron = pkgs.stdenv.mkDerivation {
        pname = "knowledge-management-system";
        version = "1.0.0";

        src = ./.;

        nativeBuildInputs = with pkgs; [
          python3
          python3Packages.pip
          python3Packages.setuptools
          makeWrapper
          nodejs
          nodePackages.npm
        ];

        buildInputs = with pkgs; [
          # Python backend dependencies (from requirements.txt)
          python3Packages.fastapi
          python3Packages.hypercorn
          python3Packages.pyyaml
          python3Packages.python-multipart
          python3Packages.pydantic

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

          # Copy web frontend source files for npm run dev
          cp -r web $out/lib/kms-electron/
          
          # Install npm dependencies for frontend server
          cd $out/lib/kms-electron/web
          npm install --production=false
          cd -

          # Copy config
          cp config.yaml $out/lib/kms-electron/

          # Copy markdown_writer.py (required by server)
          cp markdown_writer.py $out/lib/kms-electron/

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
          description = "Knowledge Management System - Electron Desktop App";
          homepage = "https://github.com/MattHandzel/KnowledgeManagementSystem";
          license = licenses.mit;
          maintainers = ["MattHandzel"];
          platforms = platforms.linux;
        };
      };
    in {
      # Package outputs
      packages = {
        default = kms-electron;
        kms-electron = kms-electron;
      };

      # App for easy running
      apps = {
        default = {
          type = "app";
          program = "${kms-electron}/bin/kms-electron";
        };
      };
    });
}
