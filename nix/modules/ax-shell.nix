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
in
{
  options.programs.ax-shell = {
    enable = lib.mkEnableOption ''
      Ax-Shell, a modern desktop shell for Hyprland compositor with customizable widgets and theming.
    '';

    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.callPackage ../packages/ax-shell.nix {};
      defaultText = lib.literalExpression "pkgs.callPackage ../packages/ax-shell.nix {}";
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
    
    keybinds = lib.mkOption {
      type = lib.types.submodule {
        options = {
          mode = lib.mkOption {
            type = lib.types.enum [ "declarative" "disabled" ];
            default = "disabled";
            description = ''
              Keybind management mode:
              - declarative: Managed via home-manager (requires wayland.windowManager.hyprland.enable = true)
              - disabled: No keybinds generated, manage manually (see README.md keybind reference)
            '';
          };

          restart = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = "SUPER ALT, B";
            example = "SUPER SHIFT, R";
            description = "Keybinding to restart ax-shell (killall + restart)";
          };
          
          launcher = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = "SUPER, R";
            example = "SUPER, SPACE";
            description = "Keybinding for application launcher";
          };

          dashboard = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = "SUPER, D";
            example = "SUPER, H";
            description = "Keybinding to open dashboard";
          };

          overview = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = "SUPER, TAB";
            example = "ALT, TAB";
            description = "Keybinding to open workspace overview";
          };

          power = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = "SUPER, ESCAPE";
            example = "SUPER SHIFT, P";
            description = "Keybinding to open power menu";
          };

          toolbox = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = "SUPER, S";
            example = null;
            description = "Keybinding to open toolbox";
          };

          pins = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER, Q";
            description = "Keybinding to open pins/bookmarks";
          };

          kanban = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER, N";
            description = "Keybinding to open kanban board";
          };

          tmux = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER, T";
            description = "Keybinding to open tmux session selector";
          };

          wallpapers = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER, COMMA";
            description = "Keybinding to open wallpaper selector";
          };

          randomWallpaper = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER SHIFT, COMMA";
            description = "Keybinding to set random wallpaper";
          };

          audioMixer = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER, M";
            description = "Keybinding to open audio mixer";
          };

          emojiPicker = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER, PERIOD";
            description = "Keybinding to open emoji picker";
          };

          clipboardHistory = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER, V";
            description = "Keybinding to open clipboard history";
          };

          bluetooth = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER, B";
            description = "Keybinding to open bluetooth manager";
          };

          toggleBar = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER CTRL, B";
            description = "Keybinding to toggle bar visibility";
          };

          toggleCaffeine = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER SHIFT, M";
            description = "Keybinding to toggle caffeine mode (disable auto-sleep)";
          };

          reloadCss = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            example = "SUPER SHIFT, B";
            description = "Keybinding to reload CSS styles";
          };
        };
      };
      default = {};
      description = ''
        Keybind configuration for ax-shell. Set mode to choose management style.
        Individual keybinds can be disabled by setting them to null.
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
              The base configuration will include swww wallpaper integration and
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
      {
        assertion = cfg.keybinds.mode != "declarative" || 
          config.home-manager.users.${cfg.user}.wayland.windowManager.hyprland.enable or false;
        message = ''
          Declarative keybind mode requires wayland.windowManager.hyprland.enable = true in home-manager.
          Either enable hyprland via home-manager or use keybinds.mode = "disabled" and manage keybinds manually.
        '';
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
      pkgs.swww      # Wallpaper daemon
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
          command = "swww"
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
    } // lib.optionalAttrs (cfg.keybinds.mode == "declarative") {
      # Declarative mode: inject keybinds into home-manager hyprland config
      wayland.windowManager.hyprland.extraConfig = ax-shell-lib.generateHyprlandKeybinds cfg.keybinds;
    };
    
  };

}
