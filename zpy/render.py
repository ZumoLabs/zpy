"""
    Utilities for Rendering in Blender.
"""
import logging
import os
import time
from pathlib import Path
from typing import Union

import zpy

import bpy
import gin

log = logging.getLogger(__name__)


def toggle_hidden(obj: bpy.types.Object, hidden: bool = True) -> None:
    """ Recursive function to make object and children invisible. """
    if obj is None:
        log.warning('Empty object given to toggle_hidden')
        return
    if hasattr(obj, 'hide_render') and hasattr(obj, 'hide_viewport'):
        # log.debug(f'Hiding object {obj.name}')
        obj.hide_render = hidden
        obj.hide_viewport = hidden
    else:
        log.warning('Object does not have hide properties')
        return
    for child in obj.children:
        toggle_hidden(child, hidden)

@gin.configurable
def _make_aov_output_node(
    output_path: Union[str, Path] = None,
    style: str = 'default',
):
    """ . """
    # Render layer node
    # bpy.types.CompositorNodeRLayers
    rl_node = bpy.context.scene.node_tree.nodes['Render Layers']
    assert style in ['rgb', 'depth', 'instance', 'category']    
    # rl_node.outputs['CATEGORY']
    # rl_node.outputs['INSTANCE']
    # rl_node.outputs['Depth']
    _tree = bpy.context.scene.node_tree
    # Visualize node shows image in workspace
    view_node = _tree.nodes.new('CompositorNodeViewer')
    view_node.inputs['Image'] = rl_node.outputs[style]
    view_node.name = f'{style} viewer'
    # File output node renders out image
    fileout_node = _tree.nodes.new('CompositorNodeOutputFile')
    fileout_node.inputs['Image'] = rl_node.outputs[style]
    fileout_node.name = f'{style} output'
    fileout_node.mute = False
    fileout_node.base_path = output_path.parent
    fileout_node.file_slots[0].path = output_path.name
    

def render_settings(
    style = '',
):
        log.debug('Using Cycles render settings.')
    scene.render.engine = "CYCLES"
    scene.render.dither_intensity = 1.0
    scene.render.filter_size = 1.5
    scene.render.use_compositing = False

    scene.cycles.samples = 128
    scene.cycles.diffuse_bounces = 4
    scene.cycles.diffuse_samples = 12
    scene.cycles.max_bounces = 4
    scene.cycles.bake_type = 'COMBINED'
    scene.cycles.use_adaptive_sampling = True

    scene.view_settings.view_transform = 'Filmic'

    scene.display.render_aa = '8'
    scene.display.viewport_aa = 'FXAA'
    scene.display.shading.color_type = 'TEXTURE'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.show_specular_highlight = True

@gin.configurable
def render_aov(
    output_path: Union[str, Path] = None,
    rgb_path: Union[str, Path] = None,
    iseg_path: Union[str, Path] = None,
    cseg_path: Union[str, Path] = None,
    width: int = 480,
    height: int = 640,
    threads: int = 4,
    render_settings: str = 'use scene',
):
    """ Render images using AOV nodes. """
    start_time = time.time()
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.threads = threads
    scene.render.image_settings.file_format = 'PNG'
    # HACK: Prevents adding frame number to filename
    scene.frame_end = scene.frame_current
    scene.frame_start = scene.frame_current
    scene.render.use_file_extension = False
    scene.render.use_stamp_frame = False
    
    if output_path is not None:
        scene.render.filepath = str(output_path)

    if render_settings == 'use scene':
        log.debug('Using whatever render setting are set in the scene.')

    elif render_settings == 'tuned cycles':
        log.debug('Using Cycles render settings.')
        scene.render.engine = "CYCLES"
        scene.render.dither_intensity = 1.0
        scene.render.filter_size = 1.5
        scene.render.use_compositing = False

        scene.cycles.samples = 128
        scene.cycles.diffuse_bounces = 4
        scene.cycles.diffuse_samples = 12
        scene.cycles.max_bounces = 4
        scene.cycles.bake_type = 'COMBINED'
        scene.cycles.use_adaptive_sampling = True

        scene.view_settings.view_transform = 'Filmic'

        scene.display.render_aa = '8'
        scene.display.viewport_aa = 'FXAA'
        scene.display.shading.color_type = 'TEXTURE'
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.show_specular_highlight = True
    else:
        raise ValueError(f'Invalid render settings {render_settings}.')
    
    output_node = bpy.context.scene.node_tree.nodes["RGB Output"]
    import pdb; pdb.set_trace()
    if output_node is not None:
        if rgb_path is not None:
            output_node.mute = False
            output_node.base_path = ''
            output_node.file_slots[0].path = str(rgb_path)
        else:
            output_node.mute = True

    output_node = bpy.context.scene.node_tree.nodes["ISEG Output"]
    if output_node is not None:
        if iseg_path is not None:
            output_node.mute = False
            output_node.base_path = ''
            output_node.file_slots[0].path = str(iseg_path)
        else:
            output_node.mute = True

    output_node = bpy.context.scene.node_tree.nodes["CSEG Output"]
    if output_node is not None:
        if cseg_path is not None:
            output_node.mute = False
            output_node.base_path = ''
            output_node.file_slots[0].path = str(cseg_path)
        else:
            output_node.mute = True

    start_time = time.time()
    bpy.ops.render.render(write_still=True)

    # HACK: Rename image outputs due to stupid Blender reasons
    if rgb_path is not None:
        _bad_name = str(rgb_path) + '%04d' % scene.frame_current
        os.rename(_bad_name, str(rgb_path))
        log.info(f'Rendering saved to {str(rgb_path)}')
    if cseg_path is not None:
        _bad_name = str(cseg_path) + '%04d' % scene.frame_current
        os.rename(_bad_name, str(cseg_path))
        log.info(f'Rendering saved to {str(cseg_path)}')
    if iseg_path is not None:
        _bad_name = str(iseg_path) + '%04d' % scene.frame_current
        os.rename(_bad_name, str(iseg_path))
        log.info(f'Rendering saved to {str(iseg_path)}')

    duration = time.time() - start_time
    log.info(f'Rendering took {duration}s to complete.')
    if log.getEffectiveLevel() == logging.DEBUG:
        _filename = f'blender-debug-scene-post-{rgb_path.stem}.blend'
        _path = rgb_path.parent / _filename
        zpy.blender.output_intermediate_scene(_path)


@gin.configurable
def render_image(output_path: Union[str, Path],
                 width: int = 480,
                 height: int = 640,
                 threads: int = 4,
                 style: str = 'default',
                 empty_background: bool = False,
                 engine: str = 'cycles',
                 ):
    """ Render an image. 

    TODO: Tune and clean up these settings.

    """
    start_time = time.time()
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = str(output_path)
    scene.render.threads = threads
    scene.render.image_settings.file_format = 'PNG'
    # TODO: The properties do not lose state when switching
    #       style, thus requiring manual-resetting.
    if style == 'default' and engine == 'cycles':
        scene.render.engine = "CYCLES"
        scene.render.film_transparent = empty_background
        scene.render.dither_intensity = 1.0
        scene.render.filter_size = 1.5
        scene.render.use_compositing = False

        scene.cycles.samples = 128
        scene.cycles.diffuse_bounces = 4
        scene.cycles.diffuse_samples = 12
        scene.cycles.max_bounces = 4
        scene.cycles.bake_type = 'COMBINED'
        scene.cycles.use_adaptive_sampling = True

        scene.view_settings.view_transform = 'Filmic'

        scene.display.render_aa = '8'
        scene.display.viewport_aa = 'FXAA'
        scene.display.shading.color_type = 'TEXTURE'
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.show_specular_highlight = True

    elif style == 'default' and engine == 'eevee':
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.film_transparent = empty_background
        scene.render.dither_intensity = 1.0
        scene.render.filter_size = 1.5
        scene.render.use_compositing = False

        scene.view_settings.view_transform = 'Filmic'

        scene.display.render_aa = '8'
        scene.display.viewport_aa = 'FXAA'
        scene.display.shading.color_type = 'TEXTURE'
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.show_specular_highlight = True

        scene.eevee.taa_render_samples = 64
        scene.eevee.taa_samples = 16
        scene.eevee.use_soft_shadows = True

        scene.eevee.use_ssr = True
        scene.eevee.use_ssr_halfres = True
        scene.eevee.ssr_quality = 0.25
        scene.eevee.ssr_thickness = 0.2
        scene.eevee.ssr_max_roughness = 0.5

        scene.eevee.use_shadow_high_bitdepth = True
        scene.eevee.use_soft_shadows = True

        scene.eevee.use_gtao = True
        scene.eevee.shadow_cube_size = '1024'
        scene.eevee.shadow_cascade_size = '1024'

    elif style == 'segmentation' and engine == 'cycles':
        scene.render.engine = "CYCLES"
        scene.render.film_transparent = True
        scene.render.dither_intensity = 0.
        scene.render.filter_size = 0.
        scene.render.use_compositing = False

        scene.cycles.samples = 1
        scene.cycles.diffuse_bounces = 0
        scene.cycles.diffuse_samples = 0
        scene.cycles.max_bounces = 0
        scene.cycles.bake_type = 'EMIT'
        scene.cycles.use_adaptive_sampling = False
        scene.cycles.use_denoising = False

        scene.view_settings.view_transform = 'Raw'

    elif style == 'segmentation' and engine == 'eevee':
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.film_transparent = True
        scene.render.dither_intensity = 0.
        scene.render.filter_size = 0.
        scene.render.use_compositing = False

        scene.display.render_aa = 'OFF'
        scene.display.viewport_aa = 'OFF'
        scene.display.shading.color_type = 'MATERIAL'
        scene.display.shading.light = 'FLAT'
        scene.display.shading.show_specular_highlight = False

        scene.view_settings.view_transform = 'Raw'

    elif style == 'hd':
        # TODO: High render settings mode.
        pass

    elif style == 'depth':
        # TODO: Depth rendering mode
        pass

    else:
        raise ValueError('Unknown render style.')
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    duration = time.time() - start_time
    log.info(
        f'Rendering {style} to {output_path.name} took {duration}s to complete.')
    if log.getEffectiveLevel() == logging.DEBUG:
        _filename = f'blender-debug-scene-post-{output_path.stem}.blend'
        _path = output_path.parent / _filename
        zpy.blender.output_intermediate_scene(_path)
