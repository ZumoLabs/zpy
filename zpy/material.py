"""
    Utilities for Materials in Blender.
"""
import logging
from pathlib import Path
from typing import Union, Tuple

import zpy
import bpy
import gin
import numpy as np

log = logging.getLogger(__name__)


@gin.configurable
def make_mat(name: str = None,
             style: str = 'segmentation',
             color: Union[Tuple[float], str] = None,
             texture_path: Union[str, Path] = None,
             engine: str = 'cycles',
             ) -> bpy.types.Material:
    """ Makes a material of a given style. """
    mat = bpy.data.materials.get(name)
    if mat is not None:
        log.debug(f'Material {name} already exists')
        return mat
    if isinstance(color, str):
        color = zpy.color.hex_to_frgb(color)
    mat = bpy.data.materials.new(name=name)
    if style == 'segmentation' and (engine == 'eevee'):
        # Segmentation uses the workbench render engine
        # and just needs a simple material with a color.
        mat.diffuse_color = color + (1.,)
        mat.shadow_method = 'NONE'
        mat.roughness = 1.0
        mat.specular_intensity = 0.0
    else:
        mat.use_nodes = True
        bsdf_node = mat.node_tree.nodes.get('Principled BSDF')
        out_node = mat.node_tree.nodes.get('Material Output')
        if style == 'segmentation' and (engine == 'cycles'):
            assert color is not None, 'Must provide color.'
            mat.node_tree.nodes.remove(bsdf_node)
            seg_node = mat.node_tree.nodes.new('ShaderNodeEmission')
            seg_node.inputs['Strength'].default_value = 1.0
            seg_node.inputs['Color'].default_value = color + (1.,)
            mat.node_tree.links.new(out_node.inputs[0], seg_node.outputs[0])
        elif style == 'diffuse_color':
            assert color is not None, 'Must provide color.'
            mat.node_tree.nodes.remove(bsdf_node)
            bsdf_node = mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            bsdf_node.inputs['Color'].default_value = color + (1.,)
            mat.node_tree.links.new(out_node.inputs[0], bsdf_node.outputs[0])
        elif style == 'texture':
            assert texture_path is not None, 'Must provide texture path.'
            tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex_node.name = 'ImageTexture'
            coord_node = mat.node_tree.nodes.new('ShaderNodeTexCoord')
            texture_path = zpy.file.verify_path(texture_path, make=False)
            bpy.ops.image.open(filepath=str(texture_path))
            tex_node.image = bpy.data.images[texture_path.name]
            tex_node.image.colorspace_settings.name = 'Filmic Log'
            mat.node_tree.links.new(tex_node.outputs[0], bsdf_node.inputs[0])
            mat.node_tree.links.new(coord_node.outputs[0], tex_node.inputs[0])
            tex_node.image.reload()
        elif style == 'depth':
            """
            TODO: Depth material.

            https://www.youtube.com/watch?v=gPwdLOSpMUA&t=435s

            https://blender.stackexchange.com/questions/42579/render-depth-map-to-image-with-python-script/42667

            """
        else:
            raise ValueError('Unknown material style.')
    log.debug(f'New material {name} - {style} color {color}')
    return mat


def set_mat(obj: Union[str, bpy.types.Object] = None,
            mat: Union[str, bpy.types.Material] = None):
    """ Sets object material. Allows strings. """
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
    for child in obj.children:
        set_mat(child, mat)
