# Module receives `self` (the flake) as first argument
self:
{
  config,
  lib,
  pkgs,
  hyprland,
  ...
}:

let
  cfg = config.programs.ax-shell;
  ax-shell-lib = import ./lib.nix { inherit lib; };

  # Get the package from the flake for this system
  defaultPackage = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
in
{
  options.programs.ax-shell = {
    enable = lib.mkEnableOption ''
      Ax-Shell, a modern desktop shell for Hyprland compositor with customizable widgets and theming.
    '';

    package = lib.mkOption {
      type = lib.types.package;
      default = defaultPackage;
      defaultText = lib.literalExpression "ax-shell.packages.\${pkgs.stdenv.hostPlatform.system}.default";
      description = ''
        The ax-shell package to use. The package will be automatically configured
        with the module settings when possible.
      '';
      apply = p: ax-shell-lib.genFinalPackage p {
        moduleConfig = cfg;
        ax-shell-lib = ax-shell-lib;
        username = cfg.user;
      };
    };

    user = lib.mkOption {
      type = lib.types.str;
      description = ''
        Username to configure ax-shell for. This user must have Hyprland enabled
        via home-manager with wayland.windowManager.hyprland.enable = true;
      '';
    };

    terminalCommand = lib.mkOption {
      type = lib.types.str;
      default = "kitty -e";
      example = "alacritty -e";
      description = ''
        Command to launch terminal applications from ax-shell.
        This should include any necessary flags for executing commands.
      '';
    };
    
    wallpapersDir = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      example = "~/Pictures/wallpapers";
      description = ''
        Directory containing wallpapers for ax-shell to use.
        When null (default), uses the example wallpapers from the nix store.
        Users can override this to point to their own wallpaper directory.
      '';
    };
    
    defaultWallpaper = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      example = lib.literalExpression "/home/user/Pictures/wallpapers/my-wallpaper.jpg";
      description = ''
        Default wallpaper to use for ~/.current.wall symlink.
        
        - If null (default): uses example-1.jpg from ax-shell's nix store assets
        - If set to a path: uses that wallpaper as default
        
        This symlink is only created if ~/.current.wall doesn't already exist,
        so it won't override existing user wallpaper selections.
      '';
    };
    
    enableGtk = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Whether to enable GTK configuration through home-manager.
        
        When true (default):
        - Configures gtk.cursorTheme in home-manager
        - Manages ~/.config/gtk-{3,4}.0/settings.ini files
        
        When false:
        - Only sets home.pointerCursor (cursor still works via X/Wayland)
        - Allows manual GTK configuration management
        - Useful when using external GTK theming (e.g., matugen-generated themes)
      '';
    };
    
    dockAlwaysOccluded = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Whether the dock should always be occluded.
        When true, the dock will remain hidden behind windows.
      '';
    };

    barWorkspaceShowNumber = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Whether to show workspace numbers in the bar.
        When true, workspace indicators will display numbers.
      '';
    };

    selectedMonitors = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [];
      example = [ "DP-1" "HDMI-A-1" ];
      description = ''
        List of monitor names to display ax-shell on.
        When empty (default), ax-shell will display on all monitors.
        Monitor names can be found using `hyprctl monitors`.
      '';
    };

    matugen = lib.mkOption {
      type = lib.types.submodule {
        options = {
          enable = lib.mkOption {
            type = lib.types.bool;
            default = true;
            description = ''
              Enable matugen integration for dynamic Material You theming.
              When enabled, generates ~/.config/matugen/config.toml and enables
              wallpaper-based color scheme generation.
            '';
          };
          
          config = lib.mkOption {
            type = lib.types.lines;
            default = "";
            description = ''
              Additional matugen configuration to append to the generated config.toml.
              The base configuration will include awww wallpaper integration and
              ax-shell template paths. Use this to add custom colors or additional templates.
              
              Example:
                [config.custom_colors.accent]
                color = "#FF5722"
                blend = true
            '';
          };
        };
      };
      default = {};
      description = ''
        Matugen configuration for dynamic theming based on wallpaper colors.
        Matugen templates are managed by ax-shell in ~/.config/Ax-Shell/config/matugen_templates/.
      '';
    };
  };
  
  config = lib.mkIf cfg.enable {
    # Basic validation
    assertions = [
      {
        assertion = cfg.user != "";
        message = "ax-shell requires a user to be specified via programs.ax-shell.user";
      }
    ];
    
    # Core functionality: install package (configs now generated in nix store)
    environment.systemPackages = [ 
      cfg.package 
      pkgs.uwsm  # Universal Wayland Session Manager - required by ax-shell
      # Runtime system dependencies that ax-shell calls via subprocess
      pkgs.hyprland  # hyprctl, hypridle, hyprlock commands
      pkgs.hyprlock
      pkgs.hypridle
      pkgs.systemd   # systemctl commands
      pkgs.procps    # pgrep, pkill commands
      pkgs.wl-clipboard  # wl-copy, wl-paste commands
      pkgs.imagemagick   # for image processing
      pkgs.libnotify     # notify-send command
      # Wallpaper and theming
      pkgs.awww      # Wallpaper daemon
      pkgs.matugen   # Material You color generator
      (pkgs.callPackage ../packages/fabric-cli.nix {})  # fabric-cli needed by matugen post_hook
      # Cursor theme for GTK apps
      pkgs.bibata-cursors
      # System monitoring
      pkgs.nvtopPackages.full  # GPU monitoring tool
    ];
    
    # Install tabler-icons font required by ax-shell for icon display
    fonts.packages = [
      (pkgs.callPackage ../packages/tabler-icons.nix {})
    ];
    
    # Set cursor theme environment variables system-wide
    environment.sessionVariables = {
      XCURSOR_THEME = "Bibata-Modern-Classic";
      XCURSOR_SIZE = "24";
    };
    
    # Configure home-manager for the specified user
    # Note: We DON'T symlink ~/.config/Ax-Shell to the nix store because:
    # - Ax-shell runs from /nix/store via the wrapper (using chdir)
    # - It needs to write runtime data to ~/.config/Ax-Shell/ (styles, state files, etc.)
    # - Templates and code are read from the nix store where ax-shell runs
    home-manager.users.${cfg.user} = {
      # Generate matugen configuration if enabled
      home.file.".config/matugen/config.toml" = lib.mkIf cfg.matugen.enable {
        text = ''
          [config]
          reload_apps = true
          
          [config.wallpaper]
          command = "awww"
          arguments = ["img", "-t", "outer", "--transition-duration", "1.5", "--transition-step", "255", "--transition-fps", "60", "-f", "Nearest"]
          set = true
          
          [templates.ax-shell]
          input_path = "${cfg.package}/lib/ax-shell/config/matugen/templates/ax-shell.css"
          output_path = "~/.config/Ax-Shell/styles/colors.css"
          post_hook = "fabric-cli exec ax-shell 'app.set_css()' &"
          
          [config.custom_colors.red]
          color = "#FF0000"
          blend = true
          
          [config.custom_colors.green]
          color = "#00FF00"
          blend = true
          
          [config.custom_colors.yellow]
          color = "#FFFF00"
          blend = true
          
          [config.custom_colors.blue]
          color = "#0000FF"
          blend = true
          
          [config.custom_colors.magenta]
          color = "#FF00FF"
          blend = true
          
          [config.custom_colors.cyan]
          color = "#00FFFF"
          blend = true
          
          [config.custom_colors.white]
          color = "#FFFFFF"
          blend = true
          
          ${cfg.matugen.config}
        '';
      };
      
      # Install cursor theme package in user profile
      home.packages = [ pkgs.bibata-cursors ];
      
      # Configure GTK cursor theme
      gtk = lib.mkIf cfg.enableGtk {
        enable = true;
        cursorTheme = {
          name = "Bibata-Modern-Classic";
          package = pkgs.bibata-cursors;
          size = 24;
        };
      };
      
      # Configure pointer cursor for all environments
      home.pointerCursor = {
        gtk.enable = cfg.enableGtk;
        name = "Bibata-Modern-Classic";
        package = pkgs.bibata-cursors;
        size = 24;
      };
      
      # Create default wallpaper symlink
      home.file.".current.wall" = {
        source = 
          if cfg.defaultWallpaper != null 
          then cfg.defaultWallpaper
          else "${cfg.package}/lib/ax-shell/assets/wallpapers_example/example-1.jpg";
        
        # This prevents clobbering - symlink only created on first activation
        # After that, user modifications are preserved
        force = false;
      };
    };
    
  };

}
