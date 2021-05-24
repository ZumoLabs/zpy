"""
    Asset management.
"""
import logging
import os
from functools import wraps
from pathlib import Path
from typing import Dict, List, Union

import bpy
import numpy as np

import gin
import zpy

log = logging.getLogger(__name__)

def get_asset_lib_path() -> Path:
    """Returns path to asset library location.

    Defaults to the directory of the blenderfile.

    Returns:
        Path: pathlib.Path object to library location.
    """

    assets_env_path = os.environ.get('ASSETS', None)
    if assets_env_path is None:
        log.warning('Could not find environment variable $ASSETS')
        # blendfile_path = bpy.path.abspath(bpy.data.filepath)
        # return Path(blendfile_path).parent
        return None
    else:
        assets_env_path = zpy.files.verify_path(assets_env_path, check_dir=True)
        log.debug(f'Found assets path at {assets_env_path}')
        return assets_env_path

def download_asset_bundle(
    bundle_name : str = '',
):
    pass
