"""
    Utilities for Rendering in Blender.
"""
import logging
import os
import time
from pathlib import Path
from typing import Union, Tuple

import bpy
import gin

import zpy

log = logging.getLogger(__name__)


@gin.configurable
def make_aov_pass(
    style: str = "instance",
) -> None:
    """Make AOV pass in Cycles."""
    scene = zpy.blender.verify_blender_scene()
    # Make sure engine is set to Cycles
    if not (scene.render.engine == "CYCLES"):
        log.warning(" Setting render engine to CYCLES to use AOV")
        scene.render.engine = "CYCLES"
        scene.render.use_compositing = True
    # Only certain styles are available
    valid_styles = ["instance", "category"]
    assert (
        style in valid_styles
    ), f"Invalid style {style} for AOV Output Node, must be in {valid_styles}."
    # Go through existing passes and make sure it doesn't exist before creating
    view_layer = zpy.blender.verify_view_layer()
    for aov in view_layer.aovs.values():
        if aov.name == style:
            log.info(f"AOV pass for {style} already exists.")
            return
    bpy.ops.scene.view_layer_add_aov()
    view_layer.aovs[-1].name = style
    view_layer.update()
    log.info(f"Created AOV pass for {style}.")


@gin.configurable
def make_aov_file_output_node(
    style: str = "rgb",
    add_hsv: bool = True,
    add_lens_dirt: bool = False,
) -> bpy.types.CompositorNodeOutputFile:
    """Make AOV Output nodes in Composition Graph."""
    log.info(f"Making AOV output node for {style}")

    # Only certain styles are available
    valid_styles = ["rgb", "depth", "instance", "category"]
    assert (
        style in valid_styles
    ), f"Invalid style {style} for AOV Output Node, must be in {valid_styles}."

    # Make sure scene composition is using nodes
    scene = zpy.blender.verify_blender_scene()
    scene.use_nodes = True
    tree = scene.node_tree

    # Remove Composite Node if it exists
    composite_node = tree.nodes.get("Composite")
    if composite_node is not None:
        tree.nodes.remove(composite_node)

    rl_node = zpy.nodes.get_or_make("Render Layers", "CompositorNodeRLayers", tree)

    # Instance and category require an AOV pass
    if style in ["instance", "category"]:
        zpy.render.make_aov_pass(style)

    # Visualize node shows image in workspace
    view_node = zpy.nodes.get_or_make(f"{style} Viewer", "CompositorNodeViewer", tree)

    # File output node renders out image
    fileout_node = zpy.nodes.get_or_make(
        f"{style} Output", "CompositorNodeOutputFile", tree
    )
    fileout_node.mute = False

    # HACK: Depth requires normalization node between layer and output
    if style == "depth":

        # Normalization node
        norm_node = zpy.nodes.get_or_make(
            f"{style} Normalize", "CompositorNodeNormalize", tree
        )

        # Negative inversion
        invert_node = zpy.nodes.get_or_make(
            f"{style} Negate", "CompositorNodeInvert", tree
        )

        # Link up the nodes
        tree.links.new(rl_node.outputs["Depth"], norm_node.inputs[0])
        tree.links.new(norm_node.outputs[0], invert_node.inputs["Color"])
        tree.links.new(invert_node.outputs[0], view_node.inputs["Image"])
        tree.links.new(invert_node.outputs[0], fileout_node.inputs["Image"])
    elif style == "rgb":
        _node = rl_node
        if add_lens_dirt:
            _node = lens_dirt_node(node_tree=tree, input_node=rl_node)
            tree.links.new(rl_node.outputs["Image"], _node.inputs["Image"])
        if add_hsv:
            _node = hsv_node(node_tree=tree, input_node=rl_node)
            tree.links.new(rl_node.outputs["Image"], _node.inputs["Image"])
        tree.links.new(_node.outputs["Image"], view_node.inputs["Image"])
        tree.links.new(_node.outputs["Image"], fileout_node.inputs["Image"])
    else:  # category and instance segmentation
        tree.links.new(rl_node.outputs[style], view_node.inputs["Image"])
        tree.links.new(rl_node.outputs[style], fileout_node.inputs["Image"])

    return fileout_node


def hsv_node(
    node_tree: bpy.types.NodeTree,
    input_node: bpy.types.Node,
) -> bpy.types.Node:
    """Adds a Hue-Saturation-Value Node."""
    hsv_node = zpy.nodes.get_or_make("HSV", "CompositorNodeHueSat", node_tree)
    node_tree.links.new(input_node.outputs["Image"], hsv_node.inputs["Image"])
    return hsv_node


def lens_dirt_node(
    node_tree: bpy.types.NodeTree,
    input_node: bpy.types.Node,
) -> bpy.types.Node:
    """TODO: Add lens dirt effect to a compositor node."""
    log.warn("NotImplemented: lens dirt ")
    return input_node


@gin.configurable
def render(
    rgb_path: Union[Path, str] = None,
    depth_path: Union[Path, str] = None,
    iseg_path: Union[Path, str] = None,
    cseg_path: Union[Path, str] = None,
    width: int = 640,
    height: int = 480,
    hsv: Tuple[float] = None,
):
    """Render images using AOV nodes."""
    scene = zpy.blender.verify_blender_scene()
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.cycles.resolution_x = width
    scene.cycles.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    # HACK: Prevents adding frame number to filename
    scene.frame_end = scene.frame_current
    scene.frame_start = scene.frame_current
    scene.render.use_file_extension = False
    scene.render.use_stamp_frame = False
    scene.render.filepath = ""

    # Create AOV output nodes
    render_outputs = {
        "rgb": rgb_path,
        "depth": depth_path,
        "instance": iseg_path,
        "category": cseg_path,
    }
    for style, output_path in render_outputs.items():
        if output_path is not None:
            # Create output node if it is not in scene
            if not scene.use_nodes:
                scene.use_nodes = True
            output_node = scene.node_tree.nodes.get(f"{style} Output", None)
            if output_node is None:
                output_node = make_aov_file_output_node(style=style)
            output_node.base_path = str(output_path.parent)
            output_node.file_slots[0].path = str(output_path.name)
            output_node.format.file_format = "PNG"
            output_node.format.color_mode = "RGB"
            if style in ["rgb"]:
                output_node.format.color_depth = "8"
                output_node.format.view_settings.view_transform = "Filmic"
                if hsv is not None:
                    hsv_node = scene.node_tree.nodes.get("HSV", None)
                    if hsv_node is not None:
                        hsv_node.inputs[1].default_value = max(0, min(hsv[0], 1))
                        hsv_node.inputs[2].default_value = max(0, min(hsv[1], 2))
                        hsv_node.inputs[3].default_value = max(0, min(hsv[2], 2))
                    else:
                        log.warn("Render given HSV but no HSV node found.")
            if style in ["depth"]:
                output_node.format.color_depth = "8"
                output_node.format.use_zbuffer = True
            if style in ["instance", "category"]:
                output_node.format.color_depth = "8"
                output_node.format.view_settings.view_transform = "Raw"
            log.debug(f"Output node for {style} image pointing to {str(output_path)}")

    if render_outputs.get("rgb", None) is not None:
        # Mute segmentation and depth output nodes
        _mute_aov_file_output_node("category", mute=True)
        _mute_aov_file_output_node("instance", mute=True)
        _mute_aov_file_output_node("depth", mute=True)
        _mute_aov_file_output_node("rgb", mute=False)
        default_render_settings()
        _render()

    cseg_is_on = render_outputs.get("category", None) is not None
    iseg_is_on = render_outputs.get("instance", None) is not None
    depth_is_on = render_outputs.get("depth", None) is not None
    if cseg_is_on or iseg_is_on or depth_is_on:
        # Un-mute segmentation and depth output nodes
        _mute_aov_file_output_node("category", mute=(not cseg_is_on))
        _mute_aov_file_output_node("instance", mute=(not iseg_is_on))
        _mute_aov_file_output_node("depth", mute=(not depth_is_on))
        _mute_aov_file_output_node("rgb", mute=True)
        segmentation_render_settings()
        _render()

    # Save intermediate blenderfile
    if log.getEffectiveLevel() == logging.DEBUG:
        # HACK: Use whatever output path is not None
        for style, output_path in render_outputs.items():
            if output_path is not None:
                break
        _filename = f"_debug.post.{output_path.stem}.blend"
        _path = output_path.parent / _filename
        zpy.blender.save_debug_blenderfile(_path)

    # HACK: Rename image outputs due to stupid Blender reasons
    for style, output_path in render_outputs.items():
        if output_path is not None:
            _bad_name = str(output_path) + "%04d" % scene.frame_current
            os.rename(_bad_name, str(output_path))
            log.info(f"Rendered {style} image saved to {str(output_path)}")


# TODO: Eventually remove this deprecated function name
def render_aov(*args, **kwargs):
    return render(*args, **kwargs)


def _mute_aov_file_output_node(style: str, mute: bool = True):
    """Mute (or un-mute) an AOV output node for a style."""
    log.debug(f"Muting AOV node for {style}")
    scene = zpy.blender.verify_blender_scene()
    node = scene.node_tree.nodes.get(f"{style} Output", None)
    if node is not None:
        node.mute = mute


@gin.configurable
def default_render_settings(
    samples: int = 96,
    tile_size: int = 48,
    spatial_splits: bool = False,
    is_aggressive: bool = False,
) -> None:
    """Render settings for normal color images.

    Args:
        samples (int, optional): Number of Cycles samples per frame
        tile_size (int, optional): Rendering tile size in pixel dimensions
        spatial_splits (bool, optional): Toogle for BVH split acceleration
        is_aggressive (bool, optional): Toogles aggressive render time reduction settings
    """
    scene = zpy.blender.verify_blender_scene()
    # Make sure engine is set to Cycles
    if not (scene.render.engine == "CYCLES"):
        log.warning(" Setting render engine to CYCLES")
        scene.render.engine == "CYCLES"

    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = False
    scene.cycles.denoiser = "OPENIMAGEDENOISE"

    scene.render.film_transparent = False
    scene.render.dither_intensity = 1.0
    scene.render.filter_size = 1.5

    view_layer = zpy.blender.verify_view_layer()
    scene.render.use_single_layer = True
    view_layer.pass_alpha_threshold = 0.5

    scene.cycles.max_bounces = 12
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transparent_max_bounces = 4
    scene.cycles.transmission_bounces = 12

    scene.cycles.sample_clamp_indirect = 2.5
    scene.cycles.sample_clamp_direct = 2.5
    scene.cycles.blur_glossy = 1
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False

    scene.view_settings.view_transform = "Filmic"
    scene.display.render_aa = "8"
    scene.display.viewport_aa = "FXAA"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.show_specular_highlight = True

    scene.render.tile_x = tile_size
    scene.render.tile_y = tile_size
    scene.cycles.debug_use_spatial_splits = spatial_splits
    scene.render.use_persistent_data = True

    if is_aggressive:
        scene.cycles.samples = 64

        scene.cycles.max_bounces = 8
        scene.cycles.diffuse_bounces = 2
        scene.cycles.glossy_bounces = 2
        scene.cycles.transparent_max_bounces = 2
        scene.cycles.transmission_bounces = 4

        scene.render.use_simplify = True
        scene.cycles.ao_bounces_render = 1
        scene.world.light_settings.use_ambient_occlusion = True
        scene.world.light_settings.distance = 40
        scene.world.light_settings.ao_factor = 0.5


def segmentation_render_settings():
    """Render settings for segmentation images."""
    scene = zpy.blender.verify_blender_scene()

    # Make sure engine is set to Cycles
    if not (scene.render.engine == "CYCLES"):
        log.warning(" Setting render engine to CYCLES")
        scene.render.engine == "CYCLES"

    scene.render.film_transparent = True
    scene.render.dither_intensity = 0.0
    scene.render.filter_size = 0.0

    scene.cycles.samples = 1
    scene.cycles.diffuse_bounces = 0
    scene.cycles.diffuse_samples = 0

    view_layer = zpy.blender.verify_view_layer()
    view_layer.pass_alpha_threshold = 0.0

    scene.cycles.max_bounces = 0
    scene.cycles.bake_type = "EMIT"
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.denoising_radius = 0

    scene.view_settings.view_transform = "Raw"

    scene.display.render_aa = "OFF"
    scene.display.viewport_aa = "OFF"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.light = "FLAT"
    scene.display.shading.show_specular_highlight = False


def _render(
    threads: int = 4,
    logfile_path: Union[Path, str] = "blender_render.log",
) -> None:
    """The actual call to render a frame in Blender.

    Args:
        threads (int, optional): Number of threads to render on. Defaults to 4.
        logfile_path (Union[Path, str]): Path to save render logfile.
    """
    start_time = time.time()
    scene = zpy.blender.verify_blender_scene()
    # TODO: Get a better default number based on number of available cores
    scene.render.threads = threads
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
        bpy.ops.render.render()
    except Exception as e:
        log.warning(f"Render raised exception {e}")
    # try:
    #     # disable output redirection
    #     os.close(1)
    #     os.dup(old)
    #     os.close(old)
    # except Exception as e:
    #     log.warning(f'Render log removal raised exception {e}')
    duration = time.time() - start_time
    log.info(f"Rendering took {duration}s to complete.")
