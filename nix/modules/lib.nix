{ lib }:

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
}
