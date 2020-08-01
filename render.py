"""
    Utilities for Rendering in Blender.
"""
import logging
import time
from pathlib import Path
from typing import Union

import bpy

from . import blender as utils_blender

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


def render_image(output_path: Union[str, Path],
                 width: int = 480,
                 height: int = 640,
                 threads: int = 4,
                 style: str = 'default',
                 empty_background: bool = False,
                 engine : str = 'cycles',
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
        scene.cycles.use_denoising = True
        scene.cycles.denoising_radius=8
        
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

        scene.eevee.taa_render_samples = 8  # 64
        scene.eevee.taa_samples = 2  # 16
        scene.eevee.sss_samples = 1  # 7
        scene.eevee.use_soft_shadows = False  # True
        scene.eevee.gi_diffuse_bounces = 1  # 3
        scene.eevee.use_gtao_bounce = False  # True
        scene.eevee.use_bloom = False  # True
        scene.eevee.use_volumetric_lights = False  # True
        scene.eevee.use_taa_reprojection = False  # True

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
        utils_blender.output_intermediate_scene(_path)
