"""
    HDRI utilities. You can find lots of free HDRIs at https://hdrihaven.com/
"""
import logging
import random
import math
from pathlib import Path
from typing import Dict, List, Tuple, Union

import bpy
import gin
import mathutils

import zpy

log = logging.getLogger(__name__)


@gin.configurable
def load_hdri(
    path: Union[str, Path],
    scale: Tuple[float] = (1.0, 1.0, 1.0),
    random_z_rot: bool = True,
) -> None:
    """ Load an HDRI from path. """
    scene = zpy.blender.verify_blender_scene()
    scene.world.use_nodes = True
    _tree = scene.world.node_tree
    # World output node
    out_node = _tree.nodes.get('World Output', None)
    if out_node is None:
        out_node = _tree.nodes.new('World Output')
    # Background node
    bg_node = _tree.nodes.get('(zpy) Background', None)
    if bg_node is None:
        bg_node = _tree.nodes.new('ShaderNodeBackground')
        bg_node.name = '(zpy) Background'
    # Texture node
    env_node = _tree.nodes.get('(zpy) Environment Texture', None)
    if env_node is None:
        env_node = _tree.nodes.new('ShaderNodeTexEnvironment')
        env_node.name = '(zpy) Environment Texture'
    log.info(f'Loading HDRI at {path}')
    path = zpy.files.verify_path(path, make=False)
    env_node.image = bpy.data.images.load(str(path))
    env_node.texture_mapping.scale = mathutils.Vector(scale)
    # Texture coordinate node
    texcoord_node = _tree.nodes.get('(zpy) Texture Coordinate', None)
    if texcoord_node is None:
        texcoord_node = _tree.nodes.new('ShaderNodeTexCoord')
        texcoord_node.name = '(zpy) Texture Coordinate'
    # World rotation node
    world_rot_node = _tree.nodes.get('(zpy) World Rotation', None)
    if world_rot_node is None:
        world_rot_node = _tree.nodes.new('ShaderNodeVectorRotate')
        world_rot_node.name = '(zpy) World Rotation'
    world_rot_node.rotation_type = 'Z_AXIS'
    if random_z_rot:
        world_rotation = random.uniform(0, math.pi)
        log.debug(f'Rotating HDRI randomly along Z axis to {world_rotation}')
        world_rot_node.inputs['Angle'].default_value = world_rotation
    # Link all the nodes together
    _tree.links.new(out_node.inputs[0], bg_node.outputs[0])
    _tree.links.new(bg_node.inputs[0], env_node.outputs[0])
    _tree.links.new(env_node.inputs[0], world_rot_node.outputs[0])
    _tree.links.new(world_rot_node.inputs[0], texcoord_node.outputs[0])


@gin.configurable
def random_hdri(
    hdri_dir: Union[str, Path] = '$ASSETS/lib/hdris/hdri_maker_lib/04k_Library',
    apply_to_scene : bool = True,
) -> Path:
    """ Generate a random HDRI from an asset path. """
    hdri_dir = zpy.files.verify_path(hdri_dir, make=False, check_dir=True)
    # Create list of HDRIs in directory
    hdris = []
    for _path in hdri_dir.iterdir():
        if _path.is_file() and _path.suffix == '.hdri':
            hdris.append(_path)
    hdri_path = random.choice(hdris)
    log.info(f'Found {len(hdris)} HDRIs, randomly chose {hdri_path.stem}')
    if apply_to_scene:
        load_hdri(hdri_path)
    return hdri_path
