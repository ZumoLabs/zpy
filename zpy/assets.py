"""
    Asset management.
"""
import logging
import os
from pathlib import Path

import bpy

import zpy

log = logging.getLogger(__name__)


def get_asset_lib_path() -> Path:
    """Returns path to asset library location.

    Defaults to the directory of the blenderfile.

    Returns:
        Path: pathlib.Path object to library location.
    """
    assets_env_path = os.environ.get("ASSETS", None)
    if assets_env_path is None:
        log.warning("Could not find environment variable $ASSETS")
        return None
    else:
        assets_env_path = zpy.files.verify_path(assets_env_path, check_dir=True)
        log.info(f"Found assets path at {assets_env_path}")
        return assets_env_path


def script_template_dir() -> Path:
    """Path to the script templates for zpy addon.

    Returns:
        pathlib.Path: Path to script templates for zpy addon.
    """
    script_path = Path(bpy.utils.script_path_user())
    template_dir = script_path / "addons" / "zpy_addon" / "templates"
    return zpy.files.verify_path(template_dir, check_dir=True)


def hdri_dir() -> Path:
    """Path to the HDRI directory.

    Returns:
        pathlib.Path: Path to HDRI directory.
    """
    asset_path = zpy.assets.get_asset_lib_path()
    if asset_path is None:
        # Path to directory containing default Blender HDRIs (exr)
        _path = Path(bpy.utils.resource_path("LOCAL"))
        hdri_dir = _path / "datafiles" / "studiolights" / "world"
    else:
        hdri_dir = asset_path / "lib" / "hdris" / "1k"
    hdri_dir = zpy.files.verify_path(hdri_dir, check_dir=True)
    log.debug(f"Using HDRI directory at {hdri_dir}")
    return hdri_dir


def texture_dir() -> Path:
    """Path to the textures directory.

    Returns:
        pathlib.Path: Path to textures directory.
    """
    asset_path = zpy.assets.get_asset_lib_path()
    if asset_path is None:
        _path = Path(bpy.utils.script_path_user())
        texture_dir = _path / "addons" / "zpy_addon" / "assets"
    else:
        texture_dir = asset_path / "lib" / "textures" / "random_512p"
    texture_dir = zpy.files.verify_path(texture_dir, check_dir=True)
    log.debug(f"Using texture directory at {texture_dir}")
    return texture_dir
