{
  description = "Ax-Shell - Modern desktop shell for Wayland compositors with NixOS integration";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Python with all ax-shell dependencies
        python-fabric = pkgs.callPackage ./nix/packages/python-fabric.nix {};
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pycairo
          dbus-python
          loguru
          psutil
          click
          ijson
          numpy
          pillow
          pywayland
          requests
          setproctitle
          toml
          watchdog
          pygobject3
          python-fabric
        ]);
      in
      {
        # Packages for direct installation
        packages = {
          ax-shell = pkgs.callPackage ./nix/packages/ax-shell.nix { flakeSrc = self; };
          fabric-cli = pkgs.callPackage ./nix/packages/fabric-cli.nix {};
          zed-fonts = pkgs.callPackage ./nix/packages/zed-fonts.nix {};
          default = self.packages.${system}.ax-shell;
        };

        # Development shell for testing ax-shell from source
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv

            # GObject introspection
            pkgs.gobject-introspection
            pkgs.wrapGAppsHook3

            # GTK and graphics libraries
            pkgs.gtk3
            pkgs.glib
            pkgs.cairo
            pkgs.gdk-pixbuf
            pkgs.pango
            pkgs.gtk-layer-shell
            pkgs.libdbusmenu-gtk3
            pkgs.gnome-bluetooth
            pkgs.cinnamon-desktop
            pkgs.vte
            pkgs.webp-pixbuf-loader

            # System services
            pkgs.networkmanager
            pkgs.upower
            pkgs.dbus
            pkgs.dbus-glib

            # Wayland
            pkgs.wayland
            pkgs.wayland-protocols

            # Runtime tools ax-shell calls
            pkgs.brightnessctl
            pkgs.cliphist
            pkgs.hyprshot
            pkgs.playerctl
            pkgs.cava
            pkgs.libnotify
            pkgs.imagemagick
            pkgs.wl-clipboard
            pkgs.procps
            pkgs.awww
            pkgs.matugen
            pkgs.socat

            # fabric-cli and gray
            (pkgs.callPackage ./nix/packages/fabric-cli.nix {})
            (pkgs.callPackage ./nix/packages/gray.nix {})

            # Cursor theme
            pkgs.bibata-cursors
          ];

          shellHook = ''
            export GDK_BACKEND=wayland
            export XDG_CURRENT_DESKTOP=Hyprland
            export XCURSOR_THEME=Bibata-Modern-Classic
            export XCURSOR_PATH="${pkgs.bibata-cursors}/share/icons"

            # Add GI typelib paths
            export GI_TYPELIB_PATH="${pkgs.lib.makeSearchPath "lib/girepository-1.0" [
              pkgs.gtk3
              pkgs.glib
              pkgs.gtk-layer-shell
              pkgs.libdbusmenu-gtk3
              pkgs.gnome-bluetooth
              pkgs.cinnamon-desktop
              pkgs.vte
              pkgs.networkmanager
              pkgs.upower
              pkgs.gdk-pixbuf
              pkgs.pango
              (pkgs.callPackage ./nix/packages/gray.nix {})
            ]}''${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"

            # Create ax-shell wrapper that runs from source
            mkdir -p .devshell/bin
            cat > .devshell/bin/ax-shell << 'WRAPPER'
            #!/usr/bin/env bash
            cd "$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")")"
            exec python main.py "$@"
            WRAPPER
            chmod +x .devshell/bin/ax-shell
            export PATH="$PWD/.devshell/bin:$PATH"

            echo "Ax-Shell dev environment loaded!"
            echo "Run: ax-shell"
          '';
        };

        # Formatter for consistent code style
        formatter = pkgs.alejandra;
      }
    ) // {
      # NixOS modules (system-independent)
      # Pass self so module can access packages
      nixosModules = {
        ax-shell = import ./nix/modules/ax-shell.nix self;
        default = self.nixosModules.ax-shell;
      };

      # Package overlays for easy integration
      overlays = {
        default = final: prev: {
          ax-shell = prev.callPackage ./nix/packages/ax-shell.nix { flakeSrc = self; };
        };
      };
    };
}
