"""
    Utilities for Materials in Blender.
"""
import logging
import copy
import random
from pathlib import Path
from typing import Tuple, Union, List

import bpy

import gin
import zpy

log = logging.getLogger(__name__)


def verify(
    mat: Union[bpy.types.Material, str],
    check_none: bool = True,
) -> bpy.types.Material:
    """Get a material given either its name or the object itself.

    Args:
        mat (Union[bpy.types.Material, str]):  Material (or it's name)
        check_none (bool, optional): Check to make sure material exists. Defaults to True.

    Raises:
        ValueError: Material does not exist.

    Returns:
        bpy.types.Material: Material object.
    """
    if isinstance(mat, str):
        mat = bpy.data.materials.get(mat)
    if check_none and mat is None:
        raise ValueError(f"Could not find material {mat}.")
    return mat


def for_mat_in_obj(
    obj: Union[bpy.types.Object, str],
) -> bpy.types.Material:
    """Yield materials in scene object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)

    Raises:
        ValueError: [description]

    Returns:
        bpy.types.Material: Material object.
    """
    obj = zpy.objects.verify(obj)
    if len(obj.material_slots) > 1:
        for mat in obj.material_slots:
            yield mat.material
    else:
        if obj.active_material is not None:
            return obj.active_material
        else:
            log.debug(f"No active material or material slots found for {obj.name}")
            return None


_SAVED_MATERIALS = {}


def save_mat_props(
    mat: Union[bpy.types.Material, str],
) -> None:
    """Save a pose (rot and pos) to dict.

    Args:
        mat (Union[bpy.types.Material, str]):  Material (or it's name)
    """
    log.info(f"Saving material properties for {mat.name}")
    _SAVED_MATERIALS[mat.name] = get_mat_props(mat)


def restore_mat_props(
    mat: Union[bpy.types.Material, str],
) -> None:
    """Restore an object to a position.

    Args:
        mat (Union[bpy.types.Material, str]):  Material (or it's name)
    """
    log.info(f"Restoring material properties for {mat.name}")
    set_mat_props(mat, _SAVED_MATERIALS[mat.name])


def restore_all_mat_props() -> None:
    """Restore all jittered materials to original look."""
    for mat_name, mat_props in _SAVED_MATERIALS.items():
        set_mat_props(mat_name, mat_props)


def get_mat_props(
    mat: Union[bpy.types.Material, str],
) -> Tuple[float]:
    """Get (some of the) material properties.

    Args:
        mat (Union[bpy.types.Material, str]):  Material (or it's name)

    Returns:
        Tuple[float]: Material property values (roughness, metallic, specular).
    """
    mat = verify(mat)
    bsdf_node = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf_node is None:
        log.warning(f"No BSDF node in {mat.name}")
        return (0.0, 0.0, 0.0)
    return (
        bsdf_node.inputs["Roughness"].default_value,
        bsdf_node.inputs["Metallic"].default_value,
        bsdf_node.inputs["Specular"].default_value,
    )


def set_mat_props(
    mat: Union[bpy.types.Material, str],
    prop_tuple: Tuple[float],
) -> None:
    """Set (some of the) material properties.

    Args:
        mat (Union[bpy.types.Material, str]):  Material (or it's name)
        prop_tuple (Tuple[float]): Material property values (roughness, metallic, specular).
    """
    mat = verify(mat)
    # TODO: Work backwards from Material output node instead of
    #       assuming a 'Principled BSDF' node
    bsdf_node = mat.node_tree.nodes.get("Principled BSDF", None)
    if bsdf_node is None:
        log.warning(f"No BSDF node in {mat.name}")
        return
    bsdf_node.inputs["Roughness"].default_value = copy.copy(prop_tuple[0])
    bsdf_node.inputs["Metallic"].default_value = copy.copy(prop_tuple[1])
    bsdf_node.inputs["Specular"].default_value = copy.copy(prop_tuple[2])


@gin.configurable
def jitter(
    mat: Union[bpy.types.Material, str],
    std: float = 0.2,
    save_first_time: bool = True,
) -> None:
    """Randomize an existing material a little.

    Args:
        mat (Union[bpy.types.Material, str]):  Material (or it's name)
        std (float, optional): Standard deviation of gaussian noise over material property. Defaults to 0.2.
        save_first_time (bool, optional): Save the material props first time jitter is called and
            restore before jittering every subsequent time. Defaults to True.
    """
    mat = verify(mat)
    if save_first_time:
        if _SAVED_MATERIALS.get(mat.name, None) is None:
            save_mat_props(mat)
        else:
            restore_mat_props(mat)
    log.info(f"Jittering material {mat.name}")
    mat_props = get_mat_props(mat)
    jittered_mat_props = tuple(map(lambda p: p + random.gauss(0, std), mat_props))
    set_mat_props(mat, jittered_mat_props)


@gin.configurable
def random_mat(
    obj: Union[bpy.types.Material, str],
    list_of_mats: List[bpy.types.Material],
    resegment: bool = True,
):
    """[summary]

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        list_of_mats (List[bpy.types.Material]): List of possible materials to choose from
        resegment (bool, optional): Re-segment the object after setting material. Defaults to True.
    """
    obj = verify(obj)
    log.debug(f"Choosing random material for obj: {obj.name}")
    _mat = random.choice(list_of_mats)
    _mat = zpy.material.verify(_mat)
    zpy.material.set_mat(obj, _mat)
    if resegment:
        # Have to re-segment the object to properly
        # set the properties on the new material
        zpy.objects.segment(
            obj, name=obj.seg.instance_name, color=obj.seg.instance_color
        )
        zpy.objects.segment(
            obj,
            as_category=True,
            name=obj.seg.category_name,
            color=obj.seg.category_color,
        )


@gin.configurable
def random_texture_mat() -> bpy.types.Material:
    """Generate a random material from a random texture image.

    Returns:
        bpy.types.Material: The newly created material.
    """
    texture_dir = zpy.assets.texture_dir()
    texture_path = zpy.files.pick_random_from_dir(
        texture_dir, suffixes=[".jpg", ".png"]
    )
    return make_mat_from_texture(texture_path, name=texture_path.stem)


@gin.configurable
def filtered_dir_texture_mat(dir_name: Union[Path, str] = None) -> bpy.types.Material:
    """Generate a material based on a word, which searches for related texture images.

    TODO: Requires Zumo Labs Asset Library

    Args:
        dir_name (Union[Path, str]): Path of directory in $ASSETS

    Returns:
        bpy.types.Material: The newly created material.
    """
    if dir_name is None:
        log.warning("No filter provided, using random texture mat instead.")
        return random_texture_mat()
    texture_dir = zpy.assets.texture_dir() / dir_name
    texture_path = zpy.files.pick_random_from_dir(
        texture_dir, suffixes=[".jpg", ".png"]
    )
    return make_mat_from_texture(texture_path, name=texture_path.stem)


@gin.configurable
def make_mat_from_texture(
    texture_path: Union[Path, str],
    name: str = None,
    coordinate: str = "uv",
) -> bpy.types.Material:
    """Makes a material from a texture image.

    Args:
        texture_path (Union[Path, str]): Path to texture image.
        name (str, optional): Name of new material.
        coordinate (str, optional): Type of texture coordinates. Values are
            "generated", "normal", "uv", "object" , defaults to "uv"

    Returns:
        bpy.types.Material: The newly created material.
    """
    texture_path = zpy.files.verify_path(texture_path, make=False)
    if name is None:
        name = texture_path.stem
    mat = bpy.data.materials.get(name, None)
    if mat is None:
        log.debug(f"Material {name} does not exist, creating it.")
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf_node = mat.node_tree.nodes.get("Principled BSDF")
    out_node = mat.node_tree.nodes.get("Material Output")
    tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex_node.name = "ImageTexture"
    coord_node = mat.node_tree.nodes.new("ShaderNodeTexCoord")
    bpy.ops.image.open(filepath=str(texture_path))
    tex_node.image = bpy.data.images[texture_path.name]
    tex_node.image.colorspace_settings.name = "Filmic Log"
    mat.node_tree.links.new(tex_node.outputs[0], bsdf_node.inputs[0])
    # TODO: Texture coordinate index is hardcoded
    valid_coordinates = ["generated", "normal", "uv", "object"]
    assert (
        coordinate in valid_coordinates
    ), f"Texture coordinate {coordinate} must be in {valid_coordinates}"
    _coord_idx = valid_coordinates.index(coordinate)
    mat.node_tree.links.new(coord_node.outputs[_coord_idx], tex_node.inputs[0])
    mat.node_tree.links.new(out_node.inputs[0], bsdf_node.outputs[0])
    tex_node.image.reload()
    return mat


@gin.configurable
def make_mat_from_color(
    color: Tuple[float],
    name: str = None,
) -> bpy.types.Material:
    """Makes a material given a color.

    Args:
        color (Tuple[float]): Color tuple (RGB).
        name (str, optional): Name of new material.

    Returns:
        bpy.types.Material: The newly created material.
    """
    if name is None:
        name = str(color)
    mat = bpy.data.materials.get(name, None)
    if mat is None:
        log.debug(f"Material {name} does not exist, creating it.")
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf_node = mat.node_tree.nodes.get("Principled BSDF")
    out_node = mat.node_tree.nodes.get("Material Output")
    mat.node_tree.nodes.remove(bsdf_node)
    bsdf_node = mat.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
    bsdf_node.inputs["Color"].default_value = color + (1.0,)
    mat.node_tree.links.new(out_node.inputs[0], bsdf_node.outputs[0])
    return mat


def set_mat(
    obj: Union[bpy.types.Object, str],
    mat: Union[bpy.types.Material, str],
    recursive: bool = True,
) -> None:
    """Set the material for an object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name) with an active material.
        mat (Union[bpy.types.Material, str]):  Material (or it's name)
        recursive (bool, optional): Recursively set material for child objects. Defaults to True.
    """
    obj = zpy.objects.verify(obj)
    mat = zpy.material.verify(mat)
    if hasattr(obj, "active_material"):
        log.debug(f"Setting object {obj.name} material {mat.name}")
        obj.active_material = mat
    else:
        log.warning("Object does not have material property")
        return
    # Recursively change material on all children of object
    if recursive:
        for child in obj.children:
            set_mat(child, mat)


@gin.configurable
def make_aov_material_output_node(
    mat: bpy.types.Material = None,
    obj: bpy.types.Object = None,
    style: str = "instance",
) -> None:
    """Make AOV Output nodes in Composition Graph.

    Args:
        mat (bpy.types.Material, optional): A blender material (either it's name or the object itself).
        obj (bpy.types.Object, optional): A blender object (either it's name or the object itself).
        style (str, optional): Type of segmentation in [instance, category]. Defaults to 'instance'.

    Raises:
        ValueError: Invalid style, no object or material given.
    """
    # Make sure engine is set to Cycles
    scene = zpy.blender.verify_blender_scene()
    if not (scene.render.engine == "CYCLES"):
        log.warning(" Setting render engine to CYCLES to use AOV")
        scene.render.engine == "CYCLES"

    # TODO: Refactor this legacy "styles" code

    # Only certain styles are available
    valid_styles = ["instance", "category"]
    assert (
        style in valid_styles
    ), f"Invalid style {style} for AOV material output node, must be in {valid_styles}."

    # HACK: multiple material slots
    all_mats = []

    # Use material
    if mat is not None:
        all_mats = [mat]
    # Get material from object
    elif obj is not None:
        if obj.active_material is None:
            log.debug(f"No active material found for {obj.name}")
            return
        if len(obj.material_slots) > 1:
            for mat in obj.material_slots:
                all_mats.append(mat.material)
        else:
            all_mats.append(obj.active_material)
    else:
        raise ValueError("Must pass in an Object or Material")

    # HACK: multiple material slots
    for mat in all_mats:

        # Make sure material is using nodes
        if not mat.use_nodes:
            mat.use_nodes = True
        tree = mat.node_tree

        # Vertex Color Node
        vcol_node = zpy.nodes.get_or_make(
            f"{style} Vertex Color", "ShaderNodeVertexColor", tree
        )
        vcol_node.layer_name = style

        # AOV Output Node
        # HACK: This type of node has a "name" property which prevents using the
        # normal zpy.nodes code due to a scope conflict with the bpy.types.Node.name property
        # See: https://docs.blender.org/api/current/bpy.types.ShaderNodeOutputAOV.html
        _name = style
        aovout_node = None
        for _node in tree.nodes:
            if _node.name == _name:
                aovout_node = _node
        if aovout_node is None:
            aovout_node = tree.nodes.new("ShaderNodeOutputAOV")
        aovout_node.name = style

        tree.links.new(vcol_node.outputs["Color"], aovout_node.inputs["Color"])
