import logging
import random
from pathlib import Path
from typing import Dict, List, Tuple, Union

import zpy

import bpy
import gin
import mathutils

log = logging.getLogger(__name__)


@gin.configurable
def load_hdri(
    path: Union[str, Path],
    scale: Tuple[float] = (1.0, 1.0, 1.0),
):
    """ Load an HDRI from path.

    Great source of HDRIs:

        https://hdrihaven.com/

    """
    log.info(f'Loading HDRI at {path}')
    path = zpy.file.verify_path(path, make=False)
    world = bpy.context.scene.world
    world.use_nodes = True
    out_node = world.node_tree.nodes.get('World Output')
    bg_node = world.node_tree.nodes.get('Background')
    env_node = world.node_tree.nodes.get('Environment Texture')
    # tex_node = world.node_tree.nodes.new('ShaderNodeTexCoord')
    if env_node is None:
        env_node = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
    env_node.image = bpy.data.images.load(str(path))
    env_node.texture_mapping.scale = mathutils.Vector(scale)
    # env_node.texture_mapping.rotation = mathutils.Vector(
    #     (0,-math.radians(90), math.radians(180)))
    # world.node_tree.links.new(env_node.inputs[0], tex_node.outputs[4])
    world.node_tree.links.new(bg_node.inputs[0], env_node.outputs[0])
    world.node_tree.links.new(out_node.inputs[0], bg_node.outputs[0])


@gin.configurable
def random_hdri(
    asset_dir: Union[str, Path] = '$ASSETS/lib/hdris/4k',
):
    """ Generate a random HDRI from an asset path. """
    asset_directory = zpy.file.verify_path(asset_dir, make=False, check_dir=True)
    return random.choice([x for x in asset_directory.iterdir() if x.is_file()])
