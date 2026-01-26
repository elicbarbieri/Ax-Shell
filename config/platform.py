"""Platform detection for Arch Linux vs NixOS compatibility."""
import os

# Canonical app name - single source of truth
APP_NAME_CAP = "Ax-Shell"


def is_nixos() -> bool:
    """Detect if running from Nix store or nix environment."""
    # Check environment variable (set by nix wrapper)
    if os.environ.get("AX_SHELL_NIX") == "1":
        return True
    # Check if running from nix store
    return os.path.abspath(__file__).startswith("/nix/store/")


def get_package_root() -> str:
    """Get ax-shell package root directory."""
    # config/platform.py -> config/ -> ax-shell root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_asset_path(relative_path: str) -> str:
    """Get absolute path to package asset."""
    return os.path.join(get_package_root(), relative_path.lstrip("./"))


def get_user_config_dir() -> str:
    """Get user config directory (~/.config/Ax-Shell)."""
    return os.path.expanduser(f"~/.config/{APP_NAME_CAP}")
