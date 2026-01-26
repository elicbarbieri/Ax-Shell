"""Shared app identifier helpers for matching window classes to desktop applications."""


def build_app_identifiers_map(all_apps):
    """
    Build a mapping of app identifiers to DesktopApp objects.

    Creates a dictionary mapping various identifiers (name, display_name,
    window_class, executable, command_line) to their corresponding DesktopApp
    objects for efficient lookups.

    Args:
        all_apps: Iterable of DesktopApp objects from get_desktop_applications()

    Returns:
        dict: Mapping of lowercase identifier strings to DesktopApp objects
    """
    identifiers = {}
    for app in all_apps:
        if app.name:
            identifiers[app.name.lower()] = app
        if app.display_name:
            identifiers[app.display_name.lower()] = app
        if app.window_class:
            identifiers[app.window_class.lower()] = app
        if app.executable:
            exe_basename = app.executable.split("/")[-1].lower()
            identifiers[exe_basename] = app
        if app.command_line:
            cmd_base = app.command_line.split()[0].split("/")[-1].lower()
            identifiers[cmd_base] = app
    return identifiers


def normalize_window_class(class_name):
    """
    Normalize window class by removing common suffixes.

    Handles common executable suffixes like .bin, .exe, -gtk etc.
    that may differ between the window class and desktop app identifiers.

    Args:
        class_name: The window class name to normalize

    Returns:
        str: Normalized lowercase class name with suffixes removed
    """
    if not class_name:
        return ""
    normalized = class_name.lower()
    suffixes = [".bin", ".exe", ".so", "-bin", "-gtk"]
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
    return normalized


def classes_match(class1, class2):
    """
    Check if two window class names match.

    Compares two class names after normalization to handle
    common variations in naming conventions.

    Args:
        class1: First class name to compare
        class2: Second class name to compare

    Returns:
        bool: True if the normalized classes match, False otherwise
    """
    if not class1 or not class2:
        return False
    norm1 = normalize_window_class(class1)
    norm2 = normalize_window_class(class2)
    return norm1 == norm2


def find_app_by_identifier(app_identifier, app_identifiers, all_apps):
    """
    Find a DesktopApp by various identifiers.

    Searches for a matching desktop application using multiple strategies:
    1. Direct lookup in pre-built identifiers map
    2. Normalized class name lookup
    3. Exact match on name, window_class, display_name
    4. Executable and command basename matching

    Args:
        app_identifier: String or dict containing app identification info.
                       If dict, searches by keys: window_class, executable,
                       command_line, name, display_name
        app_identifiers: Pre-built dict mapping identifiers to DesktopApp objects
        all_apps: Full list of DesktopApp objects for fallback searching

    Returns:
        DesktopApp object if found, None otherwise
    """
    if not app_identifier:
        return None

    # Handle dict-style identifiers (e.g., from pinned apps config)
    if isinstance(app_identifier, dict):
        for key in ["window_class", "executable", "command_line", "name", "display_name"]:
            if key in app_identifier and app_identifier[key]:
                app = _find_app_by_key(app_identifier[key], app_identifiers, all_apps)
                if app:
                    return app
        return None

    return _find_app_by_key(app_identifier, app_identifiers, all_apps)


def _find_app_by_key(key_value, app_identifiers, all_apps):
    """
    Find a DesktopApp by a single key value.

    Internal helper that performs the actual lookup using multiple strategies.

    Args:
        key_value: The identifier value to search for
        app_identifiers: Pre-built dict mapping identifiers to DesktopApp objects
        all_apps: Full list of DesktopApp objects for fallback searching

    Returns:
        DesktopApp object if found, None otherwise
    """
    if not key_value:
        return None

    normalized_id = str(key_value).lower()

    # Try direct lookup in identifiers map
    if normalized_id in app_identifiers:
        return app_identifiers[normalized_id]

    # Try with normalized class name
    norm_id = normalize_window_class(normalized_id)
    if norm_id in app_identifiers:
        return app_identifiers[norm_id]

    # Fallback: exact matching on various app properties
    for app in all_apps:
        if app.name and app.name.lower() == normalized_id:
            return app
        if app.window_class and app.window_class.lower() == normalized_id:
            return app
        if app.display_name and app.display_name.lower() == normalized_id:
            return app
        if app.executable:
            exe_base = app.executable.split("/")[-1].lower()
            if exe_base == normalized_id:
                return app
        if app.command_line:
            cmd_base = app.command_line.split()[0].split("/")[-1].lower()
            if cmd_base == normalized_id:
                return app

    return None
