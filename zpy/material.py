"""
    Utilities for Materials in Blender.
"""
import logging
import random
from pathlib import Path
from typing import Tuple, Union

import bpy
import gin
import numpy as np

import zpy

log = logging.getLogger(__name__)


@gin.configurable
def make_aov_material_output_node(
    mat: bpy.types.Material = None,
    obj: bpy.types.Object = None,
    style: str = 'instance',
) -> None:
    """ Make AOV Output nodes in Composition Graph. """
    # Make sure engine is set to Cycles
    if not (bpy.context.scene.render.engine == "CYCLES"):
        log.warning(' Setting render engine to CYCLES to use AOV')
        bpy.context.scene.render.engine == "CYCLES"
    # Only certain styles are available
    valid_styles = ['instance', 'category']
    assert style in valid_styles, \
        f'Invalid style {style} for AOV material output node, must be in {valid_styles}.'

    # HACK: multiple material slots
    all_mats = []

    # Use material
    if mat is not None:
        all_mats = [mat]
    # Get material from object
    elif obj is not None:
        if obj.active_material is None:
            log.debug(f'No active material found for {obj.name}')
            return
        if len(obj.material_slots) > 1:
            for mat in obj.material_slots:
                all_mats.append(mat.material)
        else:
            all_mats.append(obj.active_material)
    else:
        raise ValueError('Must pass in an Object or Material')

    # HACK: multiple material slots
    for mat in all_mats:

        # Make sure material is using nodes
        if not mat.use_nodes:
            mat.use_nodes = True
        _tree = mat.node_tree

        # Vertex Color Node
        _name = f'{style} Vertex Color'
        vertexcolor_node = _tree.nodes.get(_name)
        if vertexcolor_node is None:
            vertexcolor_node = _tree.nodes.new('ShaderNodeVertexColor')
        vertexcolor_node.layer_name = style
        vertexcolor_node.name = _name

        # AOV Output Node
        _name = style
        # HACK: property "name" of ShaderNodeOutputAOV behaves strangely with .get()
        aovoutput_node = None
        for _node in _tree.nodes:
            if _node.name == _name:
                aovoutput_node = _node
        if aovoutput_node is None:
            aovoutput_node = _tree.nodes.new('ShaderNodeOutputAOV')
        aovoutput_node.name = style
        _tree.links.new(vertexcolor_node.outputs['Color'],
                        aovoutput_node.inputs['Color'])


@gin.configurable
def jitter(
    mat: bpy.types.Material = None,
    roughness_std: float = 0.2,
    metallic_std: float = 0.2,
    specular_std: float = 0.2,
) -> None:
    "Randomize a real texture a little."

    bsdf_node = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf_node is None:
        log.warning(f'No BSDF node to jitter for material {mat.name}')
        return
    bsdf_node.inputs['Roughness'].default_value += random.gauss(
        0, roughness_std)
    bsdf_node.inputs['Metallic'].default_value += random.gauss(
        0, metallic_std)
    bsdf_node.inputs['Specular'].default_value += random.gauss(
        0, specular_std)


@gin.configurable
def make_mat(
    name: str = None,
    texture_path: Union[str, Path] = None,
    color: Tuple[float] = None,
) -> bpy.types.Material:
    """ Makes a material from a texture or color."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        log.debug(f'Material {name} already exists')
        return mat
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf_node = mat.node_tree.nodes.get('Principled BSDF')
    out_node = mat.node_tree.nodes.get('Material Output')
    if color is not None:
        mat.node_tree.nodes.remove(bsdf_node)
        bsdf_node = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
        bsdf_node.inputs['Color'].default_value = color + (1.,)
        mat.node_tree.links.new(out_node.inputs[0], bsdf_node.outputs[0])
    elif texture_path is not None:
        assert texture_path is not None, 'Must provide texture path.'
        tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_node.name = 'ImageTexture'
        coord_node = mat.node_tree.nodes.new('ShaderNodeTexCoord')
        texture_path = zpy.files.verify_path(texture_path, make=False)
        bpy.ops.image.open(filepath=str(texture_path))
        tex_node.image = bpy.data.images[texture_path.name]
        tex_node.image.colorspace_settings.name = 'Filmic Log'
        mat.node_tree.links.new(tex_node.outputs[0], bsdf_node.inputs[0])
        mat.node_tree.links.new(coord_node.outputs[0], tex_node.inputs[0])
        tex_node.image.reload()
    else:
        raise ValueError('make_mat requries either color or texture path.')
    return mat


def set_mat(
    obj: Union[str, bpy.types.Object] = None,
    mat: Union[str, bpy.types.Material] = None,
    recursive: bool = True,
) -> None:
    """ Recursively sets object material.

    Allows string material and object names as input.
    """
    if obj is None:
        log.warning('Empty object.')
        return
    if mat is None:
        log.warning('Empty material.')
        return
    if type(obj) == str:
        obj = bpy.data.objects.get(obj)
        if obj is None:
            log.warning(f'Could not find object {obj}.')
            return
    if type(mat) == str:
        mat = bpy.data.materials.get(mat)
        if mat is None:
            log.warning(f'Could not find material {mat}.')
            return
    if hasattr(obj, 'active_material'):
        log.debug(f'Setting object {obj.name} material {mat.name}')
        obj.active_material = mat
    else:
        log.warning('Object does not have material property')
        return
    # Recursively change material on all children of object
    if recursive:
        for child in obj.children:
            set_mat(child, mat)
