"""
    Utilities for Rendering in Blender.
"""
import logging
import os
import sys
import time
from pathlib import Path
from typing import Union, Tuple

import bpy
import gin

import zpy

log = logging.getLogger(__name__)


@gin.configurable
def make_aov_pass(
    style: str = 'instance',
) -> None:
    """ Make AOV pass in Cycles. """
    # Make sure engine is set to Cycles
    if not (bpy.context.scene.render.engine == "CYCLES"):
        log.warning(' Setting render engine to CYCLES to use AOV')
        bpy.context.scene.render.engine = "CYCLES"
        bpy.context.scene.render.use_compositing = True
    # Only certain styles are available
    valid_styles = ['instance', 'category']
    assert style in valid_styles, \
        f'Invalid style {style} for AOV Output Node, must be in {valid_styles}.'
    # Go through existing passes and make sure it doesn't exist before creating
    if bpy.context.view_layer['cycles'].get('aovs', None) is not None:
        for aov in bpy.context.view_layer['cycles']['aovs']:
            if aov['name'] == style:
                log.info(f'AOV pass for {style} already exists.')
                return
    bpy.ops.cycles.add_aov()
    bpy.context.view_layer['cycles']['aovs'][-1]['name'] = style
    bpy.context.view_layer.update()
    log.info(f'Created AOV pass for {style}.')


@gin.configurable
def make_aov_file_output_node(
    style: str = 'rgb',
    add_hsv: bool = True,
    add_lens_dirt: bool = False,
) -> bpy.types.CompositorNodeOutputFile:
    """ Make AOV Output nodes in Composition Graph. """
    log.info(f'Making AOV output node for {style}')

    # Only certain styles are available
    valid_styles = ['rgb', 'depth', 'instance', 'category']
    assert style in valid_styles, \
        f'Invalid style {style} for AOV Output Node, must be in {valid_styles}.'

    # Make sure scene composition is using nodes
    if not bpy.context.scene.use_nodes:
        bpy.context.scene.use_nodes = True
    _tree = bpy.context.scene.node_tree

    # Get or create render layer node
    if _tree.nodes.get('Render Layers', None) is None:
        rl_node = _tree.nodes.new('CompositorNodeRLayers')
    else:
        rl_node = _tree.nodes['Render Layers']
    # assert rl_node.outputs.get(style, None) is not None, \
    #     f'Render Layer output {style} does not exist.'

    # Remove Composite Node if it exists
    composite_node = _tree.nodes.get('Composite')
    if composite_node is not None:
        _tree.nodes.remove(composite_node)

    # Instance and category require an AOV pass
    if style in ['instance', 'category']:
        zpy.render.make_aov_pass(style)

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
        # Normalization node
        _name = f'{style} normalize'
        norm_node = _tree.nodes.get(_name)
        if norm_node is None:
            norm_node = _tree.nodes.new('CompositorNodeNormalize')
        norm_node.name = _name

        # Negative inversion
        _name = f'{style} negate'
        invert_node = _tree.nodes.get(_name)
        if invert_node is None:
            invert_node = _tree.nodes.new('CompositorNodeInvert')
        invert_node.name = _name

        # Link up the nodes
        _tree.links.new(rl_node.outputs['Depth'], norm_node.inputs[0])
        _tree.links.new(norm_node.outputs[0], invert_node.inputs['Color'])
        _tree.links.new(invert_node.outputs[0], view_node.inputs['Image'])
        _tree.links.new(invert_node.outputs[0], fileout_node.inputs['Image'])
    elif style == 'rgb':
        _node = rl_node
        if add_lens_dirt:
            _node = lens_dirt_node(
                node_tree=_tree,
                input_node=rl_node
            )
            _tree.links.new(rl_node.outputs['Image'], _node.inputs['Image'])
        if add_hsv:
            _node = hsv_node(
                node_tree=_tree,
                input_node=rl_node
            )
            _tree.links.new(rl_node.outputs['Image'], _node.inputs['Image'])
        _tree.links.new(_node.outputs['Image'], view_node.inputs['Image'])
        _tree.links.new(_node.outputs['Image'], fileout_node.inputs['Image'])
    else:  # category and instance segmentation
        _tree.links.new(rl_node.outputs[style], view_node.inputs['Image'])
        _tree.links.new(rl_node.outputs[style], fileout_node.inputs['Image'])

    return fileout_node


def lens_dirt_node(
    node_tree: bpy.types.NodeTree,
    input_node: bpy.types.Node,
) -> bpy.types.Node:
    """ Add lens dirt effect to a compositor node. """
    # TODO: @kursad code to create dirt effect here.
    log.warn("NotImplemented: lens dirt ")
    return input_node


def hsv_node(
    node_tree: bpy.types.NodeTree,
    input_node: bpy.types.Node,
) -> bpy.types.Node:
    """ Adds a Hue-Saturation-Value Node."""
    hsv_node = node_tree.nodes.new('CompositorNodeHueSat')
    hsv_node.name = 'hsv'
    node_tree.links.new(input_node.outputs['Image'], hsv_node.inputs['Image'])
    return hsv_node


@gin.configurable
def render_aov(
    rgb_path: Union[str, Path] = None,
    depth_path: Union[str, Path] = None,
    iseg_path: Union[str, Path] = None,
    cseg_path: Union[str, Path] = None,
    width: int = 640,
    height: int = 480,
    hsv: Tuple[float] = None,
):
    """ Render images using AOV nodes. """
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.cycles.resolution_x = width
    scene.cycles.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'

    # HACK: Prevents adding frame number to filename
    scene.frame_end = scene.frame_current
    scene.frame_start = scene.frame_current
    scene.render.use_file_extension = False
    scene.render.use_stamp_frame = False

    # Create AOV output nodes
    render_outputs = {
        'rgb': rgb_path,
        'depth': depth_path,
        'instance': iseg_path,
        'category': cseg_path,
    }
    for style, output_path in render_outputs.items():
        if output_path is not None:
            # Create output node if it is not in scene
            if not scene.use_nodes:
                scene.use_nodes = True
            output_node = scene.node_tree.nodes.get(
                f'{style} output', None)
            if output_node is None:
                output_node = make_aov_file_output_node(style=style)
            output_node.base_path = str(output_path.parent)
            output_node.file_slots[0].path = str(output_path.name)
            output_node.format.file_format = 'PNG'
            output_node.format.color_mode = 'RGB'
            if style in ['rgb']:
                output_node.format.color_depth = '8'
                output_node.format.view_settings.view_transform = 'Filmic'
                if hsv is not None:
                    hsv_node = scene.node_tree.nodes.get('hsv', None)
                    if hsv_node is not None:
                        hsv_node.inputs[1].default_value = max(0, min(hsv[0], 1))
                        hsv_node.inputs[2].default_value = max(0, min(hsv[1], 2))
                        hsv_node.inputs[3].default_value = max(0, min(hsv[2], 2))
                    else:
                        log.warn('Render given HSV but no HSV node found.')
            if style in ['depth']:
                output_node.format.color_depth = '8'
                output_node.format.use_zbuffer = True
            if style in ['instance', 'category']:
                output_node.format.color_depth = '8'
                output_node.format.view_settings.view_transform = 'Raw'
            log.debug(
                f'Output node for {style} image pointing to {str(output_path)}')

    if render_outputs.get('rgb', None) is not None:
        # Mute segmentation and depth output nodes
        _mute_aov_file_output_node('category', mute=True)
        _mute_aov_file_output_node('instance', mute=True)
        _mute_aov_file_output_node('depth', mute=True)
        _mute_aov_file_output_node('rgb', mute=False)
        _rgb_render_settings()
        _render()

    cseg_is_on = (render_outputs.get('category', None) is not None)
    iseg_is_on = (render_outputs.get('instance', None) is not None)
    depth_is_on = (render_outputs.get('depth', None) is not None)
    if cseg_is_on or iseg_is_on or depth_is_on:
        # Un-mute segmentation and depth output nodes
        _mute_aov_file_output_node('category', mute=(not cseg_is_on))
        _mute_aov_file_output_node('instance', mute=(not iseg_is_on))
        _mute_aov_file_output_node('depth', mute=(not depth_is_on))
        _mute_aov_file_output_node('rgb', mute=True)
        _seg_render_settings()
        _render()

    # Save intermediate scene
    if log.getEffectiveLevel() == logging.DEBUG:
        # HACK: Use whatever output path is not None
        for style, output_path in render_outputs.items():
            if output_path is not None:
                break
        _filename = f'blender-debug-scene-post-aov-{output_path.stem}.blend'
        _path = output_path.parent / _filename
        zpy.blender.output_intermediate_scene(_path)

    # HACK: Rename image outputs due to stupid Blender reasons
    for style, output_path in render_outputs.items():
        if output_path is not None:
            _bad_name = str(output_path) + '%04d' % scene.frame_current
            os.rename(_bad_name, str(output_path))
            log.info(f'Rendered {style} image saved to {str(output_path)}')


def _mute_aov_file_output_node(style: str, mute: bool = True):
    """ Mute (or un-mute) an AOV output node for a style. """
    log.debug(f'Muting AOV node for {style}')
    scene = bpy.context.scene
    _output_node = scene.node_tree.nodes.get(f'{style} output', None)
    if _output_node is not None:
        _output_node.mute = mute


def _rgb_render_settings():
    """ Render settings for normal color images. """
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.render.film_transparent = False
    scene.render.dither_intensity = 1.0
    scene.render.filter_size = 1.5

    scene.cycles.samples = 128
    scene.cycles.diffuse_bounces = 4
    scene.cycles.diffuse_samples = 12

    scene.view_layers[0].pass_alpha_threshold = 0.5

    scene.cycles.max_bounces = 4
    scene.cycles.bake_type = 'COMBINED'
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    scene.cycles.denoising_radius = 8

    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.cycles.denoiser = 'OPENIMAGEDENOISE'

    scene.view_settings.view_transform = 'Filmic'
    # scene.sequencer_colorspace_settings.name = 'Filmic Log'

    scene.display.render_aa = '8'
    scene.display.viewport_aa = 'FXAA'
    scene.display.shading.color_type = 'TEXTURE'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.show_specular_highlight = True


def _seg_render_settings():
    """ Render settings for segmentation images. """
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.render.film_transparent = True
    scene.render.dither_intensity = 0.
    scene.render.filter_size = 0.

    scene.cycles.samples = 1
    scene.cycles.diffuse_bounces = 0
    scene.cycles.diffuse_samples = 0

    scene.view_layers[0].pass_alpha_threshold = 0.0

    scene.cycles.max_bounces = 0
    scene.cycles.bake_type = 'EMIT'
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.denoising_radius = 0

    scene.view_settings.view_transform = 'Raw'
    # scene.sequencer_colorspace_settings.name = 'Raw'

    # scene.world.use_nodes=False
    # scene.display_settings.display_device = 'None'

    scene.display.render_aa = 'OFF'
    scene.display.viewport_aa = 'OFF'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.light = 'FLAT'
    scene.display.shading.show_specular_highlight = False


def _render(threads: int = 4,
            logfile: str = 'blender_render.log',
            ):
    """ Render in Blender. """
    start_time = time.time()
    bpy.context.scene.render.threads = threads
    # TODO: The commented out code here only works on Linux (fails on Windows)
    # try:
    #     # HACK: This disables the blender log by redirecting output to log file
    #     # https://blender.stackexchange.com/questions/44560
    #     open(logfile, 'a').close()
    #     old = os.dup(1)
    #     sys.stdout.flush()
    #     os.close(1)
    #     os.open(logfile, os.O_WRONLY)
    # except Exception as e:
    #     log.warning(f'Render log removal raised exception {e}')
    try:
        # This is the actual render call
        bpy.ops.render.render(write_still=True)
    except Exception as e:
        log.warning(f'Render raised exception {e}')
    # try:
    #     # disable output redirection
    #     os.close(1)
    #     os.dup(old)
    #     os.close(old)
    # except Exception as e:
    #     log.warning(f'Render log removal raised exception {e}')
    duration = time.time() - start_time
    log.info(f'Rendering took {duration}s to complete.')
