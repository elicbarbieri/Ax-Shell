import json
import os
import shutil

import gi
import toml

gi.require_version("Gtk", "3.0")
from fabric.utils.helpers import exec_shell_command_async

# Importar settings_constants para DEFAULTS
from . import settings_constants
from .data import (  # CONFIG_DIR, HOME_DIR no se usan aquí directamente
    APP_NAME,
    APP_NAME_CAP,
    get_default,
)

# Global variable to store binding variables, managed by this module
bind_vars = {}  # Se inicializa vacío, load_bind_vars lo poblará


def get_bind_var(setting_str: str):
    return bind_vars.get(setting_str, get_default(setting_str))


def deep_update(target: dict, update: dict) -> dict:
    """
    Recursively update a nested dictionary with values from another dictionary.
    Modifies target in-place.
    """
    for key, value in update.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            # Si el valor es un diccionario y la clave ya existe en target como diccionario,
            # entonces actualiza recursivamente.
            deep_update(target[key], value)
        else:
            # De lo contrario, simplemente establece/sobrescribe el valor.
            target[key] = value
    return target  # Aunque modifica in-place, devolverlo es una convención común


def ensure_matugen_config():
    """
    Ensure that the matugen configuration file exists and is updated
    with the expected settings.
    """
    expected_config = {
        "config": {
            "reload_apps": True,
            "wallpaper": {
                "command": "awww",
                "arguments": [
                    "img",
                    "-t",
                    "fade",
                    "--transition-duration",
                    "0.5",
                    "--transition-step",
                    "255",
                    "--transition-fps",
                    "60",
                    "-f",
                    "Nearest",
                ],
                "set": True,
            },
            "custom_colors": {
                "red": {"color": "#FF0000", "blend": True},
                "green": {"color": "#00FF00", "blend": True},
                "yellow": {"color": "#FFFF00", "blend": True},
                "blue": {"color": "#0000FF", "blend": True},
                "magenta": {"color": "#FF00FF", "blend": True},
                "cyan": {"color": "#00FFFF", "blend": True},
                "white": {"color": "#FFFFFF", "blend": True},
            },
        },
        "templates": {
            "hyprland": {
                "input_path": f"~/.config/{APP_NAME_CAP}/config/matugen/templates/hyprland-colors.conf",
                "output_path": f"~/.config/{APP_NAME_CAP}/config/hypr/colors.conf",
            },
            f"{APP_NAME}": {
                "input_path": f"~/.config/{APP_NAME_CAP}/config/matugen/templates/{APP_NAME}.css",
                "output_path": f"~/.config/{APP_NAME_CAP}/styles/colors.css",
                "post_hook": f"fabric-cli exec {APP_NAME} 'app.set_css()' &",
            },
        },
    }

    config_path = os.path.expanduser("~/.config/matugen/config.toml")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    existing_config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                existing_config = toml.load(f)
            shutil.copyfile(config_path, config_path + ".bak")
        except toml.TomlDecodeError:
            print(
                f"Warning: Could not decode TOML from {config_path}. A new default config will be created."
            )
            existing_config = {}  # Resetear si está corrupto
        except Exception as e:
            print(f"Error reading or backing up {config_path}: {e}")
            # existing_config podría estar parcialmente cargado o vacío.
            # Continuar para intentar fusionar con defaults.

    # Usamos una copia de existing_config para deep_update si no queremos modificarlo directamente
    # o asegurarse que deep_update no lo haga si no es deseado.
    # La implementación actual de deep_update modifica 'target'.
    # Para ser más seguros, podemos pasar una copia si existing_config no debe cambiar.
    # merged_config = deep_update(existing_config.copy(), expected_config)
    # O si existing_config puede ser modificado:
    merged_config = deep_update(
        existing_config, expected_config
    )  # existing_config se modifica in-place

    try:
        with open(config_path, "w") as f:
            toml.dump(merged_config, f)
    except Exception as e:
        print(f"Error writing matugen config to {config_path}: {e}")

    current_wall = os.path.expanduser("~/.current.wall")
    hypr_colors = os.path.expanduser(
        f"~/.config/{APP_NAME_CAP}/config/hypr/colors.conf"
    )
    css_colors = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/styles/colors.css")

    if (
        not os.path.exists(current_wall)
        or not os.path.exists(hypr_colors)
        or not os.path.exists(css_colors)
    ):
        os.makedirs(os.path.dirname(hypr_colors), exist_ok=True)
        os.makedirs(os.path.dirname(css_colors), exist_ok=True)

        image_path = ""
        if not os.path.exists(current_wall):
            from .platform import get_asset_path
            example_wallpaper_path = get_asset_path("assets/wallpapers_example/example-1.jpg")
            if os.path.exists(example_wallpaper_path):
                try:
                    # Si ya existe (posiblemente un enlace roto o archivo regular), eliminar y re-enlazar
                    if os.path.lexists(
                        current_wall
                    ):  # lexists para no seguir el enlace si es uno
                        os.remove(current_wall)
                    os.symlink(example_wallpaper_path, current_wall)
                    image_path = example_wallpaper_path
                except Exception as e:
                    print(f"Error creating symlink for wallpaper: {e}")
        else:
            image_path = (
                os.path.realpath(current_wall)
                if os.path.islink(current_wall)
                else current_wall
            )

        if image_path and os.path.exists(image_path):
            print(f"Generating color theme from wallpaper: {image_path}")
            try:
                matugen_cmd = f"matugen image '{image_path}'"
                exec_shell_command_async(matugen_cmd)
                print("Matugen color theme generation initiated.")
            except FileNotFoundError:
                print("Error: matugen command not found. Please install matugen.")
            except Exception as e:
                print(f"Error initiating matugen: {e}")
        elif not image_path:
            print(
                "Warning: No wallpaper path determined to generate matugen theme from."
            )
        else:  # image_path existe pero el archivo no
            print(
                f"Warning: Wallpaper at {image_path} not found. Cannot generate matugen theme."
            )


def load_bind_vars():
    """
    Load saved key binding variables from JSON, if available.
    Populates the global `bind_vars` in-place.
    """
    global bind_vars  # Necesario para modificar el objeto global bind_vars

    # 1. Limpiar el diccionario bind_vars existente.
    bind_vars.clear()
    # 2. Actualizarlo con una copia de DEFAULTS.
    bind_vars.update(
        settings_constants.DEFAULTS.copy()
    )  # Usar .copy() para no modificar DEFAULTS accidentalmente

    config_json = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config/config.json")
    if os.path.exists(config_json):
        try:
            with open(config_json, "r") as f:
                saved_vars = json.load(f)
                # 3. Usar deep_update para fusionar saved_vars en el bind_vars existente.
                deep_update(bind_vars, saved_vars)

                # La lógica para asegurar la estructura de diccionarios anidados
                # como 'metrics_visible' y 'metrics_small_visible'
                # debe operar sobre el 'bind_vars' ya actualizado.
                for vis_key in ["metrics_visible", "metrics_small_visible"]:
                    # Asegurar que la clave exista en DEFAULTS como referencia de estructura
                    if vis_key in settings_constants.DEFAULTS:
                        default_sub_dict = settings_constants.DEFAULTS[vis_key]
                        # Si la clave no está en bind_vars o no es un diccionario después de deep_update,
                        # restaurarla desde una copia de DEFAULTS para esa clave.
                        if not isinstance(bind_vars.get(vis_key), dict):
                            bind_vars[vis_key] = default_sub_dict.copy()
                        else:
                            # Si es un diccionario, asegurar que todas las sub-claves de DEFAULTS estén presentes.
                            current_sub_dict = bind_vars[vis_key]
                            for m_key, m_val in default_sub_dict.items():
                                if m_key not in current_sub_dict:
                                    current_sub_dict[m_key] = m_val
        except json.JSONDecodeError:
            print(
                f"Warning: Could not decode JSON from {config_json}. Using defaults (already initialized)."
            )
            # bind_vars ya está poblado con DEFAULTS, no se necesita acción adicional aquí.
        except Exception as e:
            print(
                f"Error loading config from {config_json}: {e}. Using defaults (already initialized)."
            )
            # bind_vars ya está poblado con DEFAULTS.
    # else:
    # Si config_json no existe, bind_vars ya está poblado con DEFAULTS.
    # print(f"Config file {config_json} not found. Using defaults (already initialized).")


def ensure_face_icon():
    """
    Ensure the face icon exists. If not, copy the default icon.
    """
    from .platform import get_asset_path

    face_icon_path = os.path.expanduser("~/.face.icon")
    default_icon_path = get_asset_path("assets/default.png")
    if not os.path.exists(face_icon_path) and os.path.exists(default_icon_path):
        try:
            shutil.copy(default_icon_path, face_icon_path)
        except Exception as e:
            print(f"Error copying default face icon: {e}")


def backup_and_replace(src: str, dest: str, config_name: str):
    """
    Backup the existing configuration file and replace it with a new one.
    """
    try:
        if os.path.exists(dest):
            backup_path = dest + ".bak"
            # Asegurarse que el directorio de backup existe si es diferente
            # os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy(dest, backup_path)
            print(f"{config_name} config backed up to {backup_path}")
        os.makedirs(
            os.path.dirname(dest), exist_ok=True
        )  # Ensure dest directory exists
        shutil.copy(src, dest)
        print(f"{config_name} config replaced from {src}")
    except Exception as e:
        print(f"Error backing up/replacing {config_name} config: {e}")


def start_config():
    """
    Run final configuration steps: ensure the matugen theme config and face
    icon exist.

    Ax-Shell no longer generates a Hyprland config fragment. Since Hyprland
    0.55 the config is Lua and `hyprland.conf` is ignored when a `hyprland.lua`
    is present, so binds/exec/window rules are set up by the user directly in
    Lua (see the README for a ready-to-use snippet).
    """
    ensure_matugen_config()
    ensure_face_icon()
