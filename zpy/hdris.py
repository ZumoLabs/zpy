"""
    HDRI utilities. You can find lots of free HDRIs at https://hdrihaven.com/
"""
import logging
import math
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Union

import bpy
import mathutils

import gin
import zpy

log = logging.getLogger(__name__)


@gin.configurable
def load_hdri(
    path: Union[Path, str],
    scale: Tuple[float] = (1.0, 1.0, 1.0),
    random_z_rot: bool = True,
) -> None:
    """ Load an HDRI from path.

    Args:
        path (Union[Path, str]): Path to the HDRI.
        scale (Tuple[float], optional): Scale in (x, y, z). Defaults to (1.0, 1.0, 1.0).
        random_z_rot (bool, optional): Randomly rotate HDRI around Z axis. Defaults to True.
    """
    scene = zpy.blender.verify_blender_scene()
    scene.world.use_nodes = True
    tree = scene.world.node_tree
    out_node = zpy.nodes.get_or_make(
        'World Output', 'ShaderNodeOutputWorld', tree, pos=(0, 0))
    bg_node = zpy.nodes.get_or_make(
        'Background', 'ShaderNodeBackground', tree, pos=(-150, 0))
    env_node = zpy.nodes.get_or_make(
        'Environment Texture', 'ShaderNodeTexEnvironment', tree, pos=(-400, 0))
    log.info(f'Loading HDRI at {path}')
    path = zpy.files.verify_path(path, make=False)
    env_node.image = bpy.data.images.load(str(path))
    env_node.texture_mapping.scale = mathutils.Vector(scale)
    world_rot_node = zpy.nodes.get_or_make(
        'World Rotation', 'ShaderNodeVectorRotate', tree, pos=(-550, 0))
    world_rot_node.rotation_type = 'Z_AXIS'
    if random_z_rot:
        world_rotation = random.uniform(0, math.pi)
        log.debug(f'Rotating HDRI randomly along Z axis to {world_rotation}')
        world_rot_node.inputs['Angle'].default_value = world_rotation
    texcoord_node = zpy.nodes.get_or_make(
        'Texture Coordinate', 'ShaderNodeTexCoord', tree, pos=(-730, 0))
    # Link all the nodes together
    tree.links.new(out_node.inputs[0], bg_node.outputs[0])
    tree.links.new(bg_node.inputs[0], env_node.outputs[0])
    tree.links.new(env_node.inputs[0], world_rot_node.outputs[0])
    tree.links.new(world_rot_node.inputs[0], texcoord_node.outputs[0])


@gin.configurable
def random_hdri(
    hdri_dir: Union[Path, str] = 'lib/hdris/1k',
    relative_to_assets_dir : bool = True,
    apply_to_scene: bool = True,
) -> Path:
    """ Generate a random HDRI from an asset path.

    Args:
        hdri_dir (Union[Path, str], optional): Path to directory with HDRIs.
        relative_to_assets_dir (bool, optional): Path is relative to the $ASSETS directory. Defaults to False.
        apply_to_scene (bool, optional): Load the HDRI into the active scene. Defaults to True.

    Returns:
        Path: Path to the random HDRI.
    """
    if relative_to_assets_dir:
        hdri_dir = zpy.blender.get_asset_lib_path().joinpath(hdri_dir)
    hdri_dir = zpy.files.verify_path(hdri_dir, check_dir=True)
    # Create list of HDRIs in directory
    hdri_paths = []
    for _path in hdri_dir.iterdir():
        if _path.is_file() and _path.suffix in ['.hdri', '.hdr']:
            hdri_paths.append(_path)
    hdri_path = random.choice(hdri_paths)
    log.info(f'Found {len(hdri_paths)} HDRIs at {hdri_dir}')
    log.info(f'Randomly picked {hdri_path.stem}')
    if apply_to_scene:
        load_hdri(hdri_path)
    return hdri_path
