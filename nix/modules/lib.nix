{ lib }:

let
  # Helper to generate a single keybind line
  mkKeybind = keybind: command: comment:
    if keybind == null then ""
    else "bind = ${keybind}, exec, ${command} # ${comment}";

  # Helper to generate fabric-send command with $fabricSend variable
  mkFabricSend = pythonCode: "\\$fabricSend '${pythonCode}'";
in

{
  # Generate final package with conditional overrides (following Hyprland pattern)
  genFinalPackage =
    pkg: args:
    let
      expectedArgs = with lib; lib.naturalSort (lib.attrNames args);
      existingArgs =
        with lib;
        naturalSort (intersectLists expectedArgs (attrNames (functionArgs pkg.override)));
    in
    if existingArgs != expectedArgs then pkg else pkg.override args;

  # Generate config file content from ax-shell configuration
  generateConfigFile = cfg:
    let
      # Handle null wallpapersDir - use empty string to trigger platform.py fallback
      # which resolves to package assets directory
      wallpapersPath = if cfg.wallpapersDir == null
        then ""  # Empty triggers get_asset_path fallback in Python
        else cfg.wallpapersDir;
    in
    builtins.toJSON {
      # Default keybindings (deprecated - use keybinds instead)
      prefix_dash = "SUPER";
      suffix_dash = "D";
      prefix_overview = "SUPER";
      suffix_overview = "TAB";
      prefix_power = "SUPER";
      suffix_power = "ESCAPE";
      prefix_restart = "SUPER ALT";
      suffix_restart = "B";
      prefix_launcher = "SUPER";
      suffix_launcher = "R";
    
      # Essential appearance settings
      wallpapers_dir = wallpapersPath;
      terminal_command = cfg.terminalCommand;
      bar_position = "Top";
      vertical = false;
      
      # Component visibility - all enabled by default
      bar_button_apps_visible = true;
      bar_systray_visible = true;
      bar_control_visible = true;
      bar_network_visible = true;
      bar_button_tools_visible = true;
      bar_sysprofiles_visible = true;
      bar_button_overview_visible = true;
      bar_ws_container_visible = true;
      bar_weather_visible = true;
      bar_battery_visible = true;
      bar_metrics_visible = true;
      bar_language_visible = true;
      bar_date_time_visible = true;
      bar_button_power_visible = true;
      
      # System settings
      dock_enabled = true;
      dock_always_occluded = cfg.dockAlwaysOccluded;
      dock_icon_size = 28;
      bar_workspace_show_number = cfg.barWorkspaceShowNumber;
      selected_monitors = cfg.selectedMonitors;
    };

  # Generate Hyprland keybinds for declarative mode (home-manager extraConfig)
  generateHyprlandKeybinds = keybinds:
    let
      home = "$HOME";
      appName = "ax-shell";
      
      binds = lib.filter (x: x != "") [
        "# Ax-Shell Keybinds (managed by NixOS)"
        ""
        "# Clipboard history daemon"
        "exec-once = wl-paste --type image --watch cliphist store"
        ""
        "# Ax-Shell variables"
        "\\$fabricSend = fabric-cli exec ${appName}"
        ""
        (mkKeybind keybinds.restart 
          "pkill -x ${appName}; ${appName}" 
          "Restart Ax-Shell")
        (mkKeybind keybinds.launcher 
          (mkFabricSend "notch.open_notch(\\\"launcher\\\")") 
          "App Launcher")
        (mkKeybind keybinds.dashboard 
          (mkFabricSend "notch.open_notch(\\\"dashboard\\\")") 
          "Dashboard")
        (mkKeybind keybinds.overview 
          (mkFabricSend "notch.open_notch(\\\"overview\\\")") 
          "Overview")
        (mkKeybind keybinds.power 
          (mkFabricSend "notch.open_notch(\\\"power\\\")") 
          "Power Menu")
        (mkKeybind keybinds.toolbox 
          (mkFabricSend "notch.open_notch(\\\"tools\\\")") 
          "Toolbox")
        (mkKeybind keybinds.pins 
          (mkFabricSend "notch.open_notch(\\\"pins\\\")") 
          "Pins")
        (mkKeybind keybinds.kanban 
          (mkFabricSend "notch.open_notch(\\\"kanban\\\")") 
          "Kanban")
        (mkKeybind keybinds.tmux 
          (mkFabricSend "notch.open_notch(\\\"tmux\\\")") 
          "Tmux")
        (mkKeybind keybinds.wallpapers 
          (mkFabricSend "notch.open_notch(\\\"wallpapers\\\")") 
          "Wallpapers")
        (mkKeybind keybinds.randomWallpaper 
          (mkFabricSend "notch.dashboard.wallpapers.set_random_wallpaper(None, external=True)") 
          "Random Wallpaper")
        (mkKeybind keybinds.audioMixer 
          (mkFabricSend "notch.open_notch(\\\"mixer\\\")") 
          "Audio Mixer")
        (mkKeybind keybinds.emojiPicker 
          (mkFabricSend "notch.open_notch(\\\"emoji\\\")") 
          "Emoji Picker")
        (mkKeybind keybinds.clipboardHistory 
          (mkFabricSend "notch.open_notch(\\\"cliphist\\\")") 
          "Clipboard History")
        (mkKeybind keybinds.bluetooth 
          (mkFabricSend "notch.open_notch(\\\"bluetooth\\\")") 
          "Bluetooth")
        (mkKeybind keybinds.toggleBar 
          (mkFabricSend "from utils.global_keybinds import get_global_keybind_handler; get_global_keybind_handler().toggle_bar()") 
          "Toggle Bar")
        (mkKeybind keybinds.toggleCaffeine 
          (mkFabricSend "notch.dashboard.widgets.buttons.caffeine_button.toggle_inhibit(external=True)") 
          "Toggle Caffeine")
        (mkKeybind keybinds.reloadCss 
          (mkFabricSend "app.set_css()") 
          "Reload CSS")
      ];
    in
    lib.concatStringsSep "\n" binds;

}
