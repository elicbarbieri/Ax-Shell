import os

import gi

gi.require_version("GLib", "2.0")
import setproctitle
from fabric import Application
from fabric.utils import exec_shell_command_async, get_relative_path
from gi.repository import GLib

from config.data import APP_NAME, APP_NAME_CAP, CACHE_DIR, CONFIG_FILE, HOME_DIR
from modules.bar import Bar
from modules.corners import Corners
from modules.dock import Dock
from modules.notch import Notch
from modules.notifications import NotificationPopup

fonts_updated_file = f"{CACHE_DIR}/fonts_updated"

# Module-level app variable for fabric-cli exec access
app = None

if __name__ == "__main__":
    setproctitle.setproctitle(APP_NAME)

    if not os.path.isfile(CONFIG_FILE):
        config_script_path = get_relative_path("config/config.py")
        exec_shell_command_async(f"python {config_script_path}")

    current_wallpaper = os.path.expanduser("~/.current.wall")
    if not os.path.exists(current_wallpaper):
        from config.platform import get_asset_path
        example_wallpaper = get_asset_path("assets/wallpapers_example/example-1.jpg")
        if os.path.exists(example_wallpaper):
            os.symlink(example_wallpaper, current_wallpaper)

    # Load configuration
    from config.data import load_config

    config = load_config()

    # Initialize multi-monitor services
    try:
        from utils.monitor_manager import get_monitor_manager
        from services.monitor_focus import get_monitor_focus_service
        from utils.global_keybinds import init_global_keybind_objects
        
        monitor_manager = get_monitor_manager()
        monitor_focus_service = get_monitor_focus_service()
        monitor_manager.set_monitor_focus_service(monitor_focus_service)
        init_global_keybind_objects()
        
        # Get all available monitors
        all_monitors = monitor_manager.get_monitors()
        multi_monitor_enabled = True
    except ImportError:
        # Fallback to single monitor mode
        all_monitors = [{'id': 0, 'name': 'default'}]
        monitor_manager = None
        multi_monitor_enabled = False
    
    # Filter monitors based on selected_monitors configuration
    selected_monitors_config = config.get("selected_monitors", [])
    
    # If selected_monitors is empty, show on all monitors (current behavior)
    if not selected_monitors_config:
        monitors = all_monitors
        print("Ax-Shell: No specific monitors selected, showing on all monitors")
    else:
        # Filter monitors to only include selected ones
        monitors = []
        selected_monitor_names = set(selected_monitors_config)
        
        for monitor in all_monitors:
            monitor_name = monitor.get('name', f'monitor-{monitor.get("id", 0)}')
            if monitor_name in selected_monitor_names:
                monitors.append(monitor)
                print(f"Ax-Shell: Including monitor '{monitor_name}' (selected)")
            else:
                print(f"Ax-Shell: Excluding monitor '{monitor_name}' (not selected)")
        
        # Fallback: if no valid monitors found, use all monitors
        if not monitors:
            print("Ax-Shell: No valid selected monitors found, falling back to all monitors")
            monitors = all_monitors
    
    # Create application components list
    app_components = []
    corners = None
    notification = None
    
    # Create components for each monitor
    for monitor in monitors:
        monitor_id = monitor['id']
        
        # Create corners only for the first monitor (shared across all)
        if monitor_id == 0:
            corners = Corners()
            # Set corners visibility based on config
            corners_visible = config.get("corners_visible", True)
            corners.set_visible(corners_visible)
            app_components.append(corners)
        
        # Create monitor-specific components
        if multi_monitor_enabled:
            bar = Bar(monitor_id=monitor_id)
            notch = Notch(monitor_id=monitor_id)
            dock = Dock(monitor_id=monitor_id)
        else:
            # Single monitor fallback
            bar = Bar()
            notch = Notch()
            dock = Dock()
        
        # Connect bar and notch
        bar.notch = notch
        notch.bar = bar
        
        # Create notification popup for the first monitor only
        if monitor_id == 0:
            notification = NotificationPopup(widgets=notch.dashboard.widgets)
            app_components.append(notification)
        
        # Register instances in monitor manager if available
        if multi_monitor_enabled and monitor_manager:
            monitor_manager.register_monitor_instances(monitor_id, {
                'bar': bar,
                'notch': notch,
                'dock': dock,
                'corners': corners if monitor_id == 0 else None
            })
        
        # Add components to app list
        app_components.extend([bar, notch, dock])

    # Create the application with all components
    app = Application(f"{APP_NAME}", *app_components)

    def set_css():
        from config.platform import get_package_root, get_user_config_dir

        # Concatenate colors.css (defines CSS variables) + main.css (uses them)
        combined_css = ""

        colors_css_path = os.path.join(get_user_config_dir(), "styles", "colors.css")
        if os.path.exists(colors_css_path):
            with open(colors_css_path, "r") as f:
                combined_css += f.read() + "\n"

        main_css_path = os.path.join(get_package_root(), "main.css")
        with open(main_css_path, "r") as f:
            combined_css += f.read()

        app.set_stylesheet_from_string(combined_css)

    app.set_css = set_css

    app.set_css()

    app.run()
