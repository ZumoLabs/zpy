"""
    Utilities for Rendering in Blender.
"""
import logging
import os
import time
from pathlib import Path
from typing import Union, List

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


def prepare_aov_scene(
    styles: List[str],
):
    """ Prepare scene for output using AOV nodes. """
    for style in styles:
        # Make AOV Pass
        make_aov_pass(style)
        # Add AOV node to every material in the scene
        for obj in bpy.data.objects:
            zpy.material.make_aov_material_output_node(obj=obj, style=style)


@gin.configurable
def make_aov_pass(
    style: str = 'instance',
):
    """ Make AOV pass in Cycles. """
    # Make sure engine is set to Cycles
    if not (bpy.context.scene.render.engine == "CYCLES"):
        log.warning(' Setting render engine to CYCLES to use AOV')
        bpy.context.scene.render.engine == "CYCLES"
    # Only certain styles are available
    valid_styles = ['instance', 'category']
    assert style in valid_styles, \
        f'Invalid style {style} for AOV Output Node, must be in {valid_styles}.'
    # Go through existing passes and make sure it doesn't exist before creating
    if bpy.context.view_layer['cycles'].get('aov', None) is not None:
        for aov in bpy.context.view_layer['cycles']['aovs']:
            if aov['name'] == style:
                log.debug(f'AOV pass for {style} already exists.')
                return
    bpy.ops.cycles.add_aov()
    bpy.context.view_layer['cycles']['aovs'][-1]['name'] = style


@gin.configurable
def make_aov_file_output_node(
    style: str = 'rgb',
) -> bpy.types.CompositorNodeOutputFile:
    """ Make AOV Output nodes in Composition Graph. """
    log.debug(f'Making AOV output node for {style}')

    # Only certain styles are available
    valid_styles = ['rgb', 'depth', 'instance', 'category']
    assert style in valid_styles, \
        f'Invalid style {style} for AOV Output Node, must be in {valid_styles}.'

    # HACK: Some styles have specific output node names
    if style == 'rgb':
        style = 'Image'
    if style == 'depth':
        style = 'Depth'

    # Make sure scene composition is using nodes
    if not bpy.context.scene.use_nodes:
        bpy.context.scene.use_nodes = True
    _tree = bpy.context.scene.node_tree

    # Get or create render layer node
    if _tree.nodes.get('Render Layers', None) is None:
        rl_node = _tree.nodes.new('CompositorNodeRLayers')
    else:
        rl_node = _tree.nodes['Render Layers']
    assert rl_node.outputs.get(style, None) is not None, \
        f'Render Layer output {style} does not exist.'

    # Remove Composite Node if it exists
    composite_node = _tree.nodes.get('Composite')
    if composite_node is not None:
        _tree.nodes.remove(composite_node)

    # Visualize node shows image in workspace
    _name = f'{style} viewer'
    view_node = _tree.nodes.get(_name)
    if view_node is None:
        view_node = _tree.nodes.new('CompositorNodeViewer')
    view_node.name = _name

    # File output node renders out image
    _name = f'{style} output'
    fileout_node = _tree.nodes.get(_name)
    if fileout_node is None:
        fileout_node = _tree.nodes.new('CompositorNodeOutputFile')
    fileout_node.name = _name
    fileout_node.mute = False

    # HACK: Depth requires normalization node between layer and output
    if style == 'depth':
        # Normalization node for viewer
        _name_viewer = f'{style} normalize viewer'
        norm_node_viewer = _tree.nodes.get(_name_viewer)
        if norm_node_viewer is None:
            norm_node_viewer = _tree.nodes.new('CompositorNodeNormalize')
        norm_node_viewer.name = _name_viewer
        
        # Normalization node for fileout
        _name_fileout = f'{style} normalize fileout'
        norm_node_fileout = _tree.nodes.get(_name_fileout)
        if norm_node_fileout is None:
            norm_node_fileout = _tree.nodes.new('CompositorNodeNormalize')
        norm_node_fileout.name = _name_fileout

        # Link up the nodes
        _tree.links.new(rl_node.outputs[style], norm_node_viewer.inputs[0])
        _tree.links.new(rl_node.outputs[style], norm_node_fileout.inputs[0])
        _tree.links.new(norm_node_viewer.outputs[0], view_node.inputs['Image'])
        _tree.links.new(
            norm_node_fileout.outputs[0], fileout_node.inputs['Image'])
    else:
        _tree.links.new(rl_node.outputs[style], view_node.inputs['Image'])
        _tree.links.new(rl_node.outputs[style], fileout_node.inputs['Image'])

    return fileout_node


@gin.configurable
def render_aov(
    rgb_path: Union[str, Path] = None,
    depth_path: Union[str, Path] = None,
    iseg_path: Union[str, Path] = None,
    cseg_path: Union[str, Path] = None,
    width: int = 480,
    height: int = 640,
    threads: int = 4,
):
    """ Render images using AOV nodes. """
    start_time = time.time()
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height

    # Adjust some render settings
    scene.render.threads = threads
    # scene.render.image_settings.file_format = 'PNG'
    # scene.view_settings.view_transform = 'Raw'
    scene.render.dither_intensity = 0.
    scene.render.film_transparent = False

    # HACK: Prevents adding frame number to filename
    scene.frame_end = scene.frame_current
    scene.frame_start = scene.frame_current
    scene.render.use_file_extension = False
    scene.render.use_stamp_frame = False

    # HACK: This causes edges of segmentation to be weird
    scene.cycles.samples = 1

    # Create AOV output nodes
    render_outputs = {
        'rgb': rgb_path,
        'depth': depth_path,
        'instance': iseg_path,
        'category': cseg_path,
    }
    for style, output_path in render_outputs.items():
        if output_path is not None:
            if not bpy.context.scene.use_nodes:
                bpy.context.scene.use_nodes = True
            output_node = bpy.context.scene.node_tree.nodes.get(
                f'{style} output', None)
            if output_node is None:
                output_node = make_aov_file_output_node(style=style)
            output_node.base_path = str(output_path.parent)
            output_node.file_slots[0].path = str(output_path.name)
            # output_node.format.color_mode = 'RGB'
            # output_node.format.color_depth = '8'
            output_node.format.use_zbuffer = True
            output_node.format.file_format = 'PNG'
            # output_node.format.view_settings.view_transform = 'Raw'
            log.debug(
                f'Output node for {style} image pointing to {str(output_path)}')

    # Printout render time
    start_time = time.time()
    try:
        bpy.ops.render.render(write_still=True)
    except Exception as e:
        log.warning(f'Render raised exception {e}')
    duration = time.time() - start_time
    log.info(f'Rendering took {duration}s to complete.')

    # HACK: Rename image outputs due to stupid Blender reasons
    for style, output_path in render_outputs.items():
        if output_path is not None:
            _bad_name = str(output_path) + '%04d' % scene.frame_current
            os.rename(_bad_name, str(output_path))
            log.info(f'Rendered {style} image saved to {str(output_path)}')

    # Save intermediate scene
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
