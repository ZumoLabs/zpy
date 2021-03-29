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
    tree: bpy.types.NodeTree,
    label_tag: str = '(zpy) ',
    pos: Tuple[float] = None,
) -> bpy.types.Node:
    """ Verify existence or create a node.

    Args:
        name (str): Name of the node.
        node_type (str): Node type e.g. "ShaderNodeBackground"
        tree (bpy.types.NodeTree): Node tree where this node will be added.
        label_tag (str, optional): Node label will include this tag to make it easier to identify within Blender. Defaults to '(zpy) '.
        pos (Tuple[float], optional): Location of the node in node editor. Defaults to None.

    Returns:
        bpy.types.Node: The newly created (or already existing) node.
    """
    node = tree.nodes.get(name, None)
    if node is None:
        node = tree.nodes.new(node_type)
        node.name = name
    node.label = f'{label_tag}{name}'
    node.bl_description = 'This node has been created and/or modified by zpy'
    if pos is not None:
        node.location = pos
    return node

def toggle_nodegroup(
    node_tree: bpy.types.NodeTree,
    state: bool = False
) -> None:
    """ Change the state of all the nodes inside a node group 
    
    Args:
        node_tree (bpy.types.NodeTree): Top level node group
        state: (bool): Toggle state
    """
    for n in node_tree.nodes:
        n.mute=state
