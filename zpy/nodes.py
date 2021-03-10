"""
    Node utilities.
"""
import logging

import bpy
import mathutils
from typing import Tuple

import gin
import zpy

log = logging.getLogger(__name__)


@gin.configurable
def get_or_make(
    name: str,
    node_type: str,
    node_tree: bpy.types.NodeTree,
    name_tag: str = '(zpy) ',
    pos: Tuple[float] = None,
) -> bpy.types.Node:
    """ Verify existence or create a node. """
    node = node_tree.nodes.get(name, None)
    if node is None:
        node = node_tree.nodes.new(node_type)
        node.name = name
    # Name tag identifies nodes created through zpy
    node.label = f'{name_tag}{name}' 
    node.bl_description = 'This node has been created and/or modified by zpy'
    if pos is not None:
        node.location = pos
    return node
