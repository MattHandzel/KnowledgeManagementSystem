{
  description = "Terminal-based knowledge capture daemon for NixOS + Hyprland";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        capture-daemon = pkgs.python3Packages.buildPythonApplication {
          pname = "capture-daemon";
          version = "0.1.0";
          
          src = ./.;
          
          propagatedBuildInputs = with pkgs.python3Packages; [
            pyyaml
            watchdog
          ];
          
          buildInputs = with pkgs; [
            ncurses
          ];
          
          # Runtime dependencies for capture functionality
          makeWrapperArgs = [
            "--prefix PATH : ${pkgs.lib.makeBinPath [
              pkgs.grim          # Screenshots
              pkgs.slurp         # Screen selection
              pkgs.wl-clipboard  # Clipboard access
              pkgs.wf-recorder   # Screen recording
              pkgs.alsa-utils    # Audio recording
            ]}"
          ];
          
          # Install scripts
          installPhase = ''
            mkdir -p $out/bin
            mkdir -p $out/lib/python${pkgs.python3.pythonVersion}/site-packages/capture_daemon
            
            # Copy Python modules
            cp *.py $out/lib/python${pkgs.python3.pythonVersion}/site-packages/capture_daemon/
            
            # Create executable scripts
            cat > $out/bin/capture-daemon << EOF
            #!${pkgs.python3}/bin/python3
            import sys
            sys.path.insert(0, '$out/lib/python${pkgs.python3.pythonVersion}/site-packages')
            from capture_daemon.capture_daemon import main
            if __name__ == '__main__':
                main()
            EOF
            
            cat > $out/bin/trigger-capture << EOF
            #!${pkgs.python3}/bin/python3
            import sys
            sys.path.insert(0, '$out/lib/python${pkgs.python3.pythonVersion}/site-packages')
            from capture_daemon.trigger_capture import main
            if __name__ == '__main__':
                main()
            EOF
            
            chmod +x $out/bin/capture-daemon
            chmod +x $out/bin/trigger-capture
            
            # Copy config
            mkdir -p $out/share/capture-daemon
            cp config.yaml $out/share/capture-daemon/
          '';
          
          meta = with pkgs.lib; {
            description = "Ultra-lightweight terminal-based knowledge capture daemon";
            homepage = "https://github.com/MattHandzel/capture-daemon";
            license = licenses.mit;
            maintainers = [ "MattHandzel" ];
            platforms = platforms.linux;
          };
        };
        
      in {
        # Development shell
        devShells.default = pkgs.mkShell {
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
            
            # Development tools
            python3Packages.pytest
            python3Packages.pytest-mock
            python3Packages.black
            python3Packages.flake8
            python3Packages.mypy
            
            # Nix tools
            nixpkgs-fmt
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
            echo "  bind = SUPER, C, exec, python ${toString ./.}/trigger_capture.py quick"
            echo "  bind = SUPER SHIFT, C, exec, python ${toString ./.}/trigger_capture.py multimodal"
            echo ""
            
            # Create required directories
            mkdir -p ~/notes/capture/raw_capture/media
            
            # Set up socket directory
            mkdir -p /tmp/capture_daemon
            
            # Make scripts executable
            chmod +x *.py
            
            export PYTHONPATH="${toString ./.}:$PYTHONPATH"
          '';
        };
        
        # Package output
        packages = {
          default = capture-daemon;
          capture-daemon = capture-daemon;
        };
        
        # App for easy running
        apps = {
          default = {
            type = "app";
            program = "${capture-daemon}/bin/capture-daemon";
          };
          
          daemon = {
            type = "app";
            program = "${capture-daemon}/bin/capture-daemon";
          };
          
          trigger = {
            type = "app";
            program = "${capture-daemon}/bin/trigger-capture";
          };
        };
        
        # NixOS module for system integration
        nixosModules.capture-daemon = { config, lib, pkgs, ... }:
          with lib;
          let
            cfg = config.services.capture-daemon;
          in {
            options.services.capture-daemon = {
              enable = mkEnableOption "Terminal capture daemon";
              
              user = mkOption {
                type = types.str;
                default = "user";
                description = "User to run the capture daemon as";
              };
              
              vaultPath = mkOption {
                type = types.str;
                default = "/home/${cfg.user}/notes";
                description = "Path to the notes vault";
              };
              
              socketPath = mkOption {
                type = types.str;
                default = "/tmp/capture_daemon.sock";
                description = "Unix socket path for daemon communication";
              };
              
              autoStart = mkOption {
                type = types.bool;
                default = true;
                description = "Whether to auto-start the daemon";
              };
            };
            
            config = mkIf cfg.enable {
              systemd.user.services.capture-daemon = {
                description = "Terminal Knowledge Capture Daemon";
                wantedBy = mkIf cfg.autoStart [ "default.target" ];
                
                serviceConfig = {
                  Type = "simple";
                  ExecStart = "${capture-daemon}/bin/capture-daemon --daemon --vault-path=${cfg.vaultPath} --socket-path=${cfg.socketPath}";
                  Restart = "on-failure";
                  RestartSec = 5;
                };
                
                environment = {
                  PATH = lib.makeBinPath [
                    pkgs.grim
                    pkgs.slurp
                    pkgs.wl-clipboard
                    pkgs.wf-recorder
                    pkgs.alsa-utils
                  ];
                };
              };
              
              environment.systemPackages = [ capture-daemon ];
            };
          };
      });
}
