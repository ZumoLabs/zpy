"""
    Object utilities for Blender Python.
"""
import logging
import random
from pathlib import Path
from typing import Any, List, Tuple, Union

import bpy
import gin
import mathutils
import numpy as np

import zpy

log = logging.getLogger(__name__)


def load_blend_obj(
        name: str,
        path: Union[str, Path],
        link: bool = False,
) -> bpy.types.Object:
    """ Load object from blend file. """
    path = zpy.files.verify_path(path, make=False)
    with bpy.data.libraries.load(str(path), link=link) as (data_from, data_to):
        for from_obj in data_from.objects:
            if from_obj.startswith(name):
                log.debug(f'Loading obj {from_obj} from {str(path)}.')
                data_to.objects.append(from_obj)
    # Copy objects over to the current scene
    for obj in data_to.objects:
        bpy.context.scene.collection.objects.link(obj)
    bpy.ops.file.find_missing_files(directory=str(path.parent / 'TEX'))
    return bpy.data.objects[name]


def select(obj: Union[bpy.types.Object, str]) -> None:
    """ Delete an object. """
    if isinstance(obj, str):
        obj = bpy.data.objects[obj]
    if obj is not None:
        # TODO: This sometimes does not work due to context issues
        log.debug(f'Selecting obj: {obj.name}')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        bpy.data.objects[obj.name].select_set(True)
    else:
        log.debug(f'Could not find object')


def delete_obj(obj: Union[bpy.types.Object, str]) -> None:
    """ Delete an object. """
    if isinstance(obj, str):
        obj = bpy.data.objects[obj]
    if obj is not None:
        log.debug(f'Removing obj: {obj.name}')
        # Make sure selected object is the active object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.delete()
        # bpy.data.objects.remove(obj, do_unlink=True)
    else:
        log.debug(f'Could not find object')


@gin.configurable
def is_inside(
    point: mathutils.Vector,
    obj: bpy.types.Object,
) -> bool:
    """ Is point inside a mesh.

    From:

    https://blender.stackexchange.com/questions/31693/how-to-find-if-a-point-is-inside-a-mesh

    """
    is_found, closest_point, normal, _ = obj.closest_point_on_mesh(point)
    if not is_found:
        return False
    p2 = closest_point - point
    v = p2.dot(normal)
    return not(v < 0.0)


def for_obj_in_selected_objs(context) -> bpy.types.Object:
    """ Safe iterable for selected objects. """
    for obj in context.selected_objects:
        # Only meshes or empty objects TODO: Why the empty objects
        if not (obj.type == 'MESH' or obj.type == 'EMPTY'):
            continue
        # Make sure object exists in the scene
        if bpy.data.objects.get(obj.name, None) is None:
            continue
        context.view_layer.objects.active = obj
        yield obj


def for_obj_in_collections(
    collections: List[bpy.types.Collection],
) -> bpy.types.Object:
    """ Yield objects in list of collection. """
    for collection in collections:
        for obj in collection.all_objects:
            if obj.type == 'MESH':
                # This gives you direct access to data block
                yield bpy.data.objects[obj.name]


def toggle_hidden(
    obj: bpy.types.Object,
    hidden: bool = True,
    filter_string: str = None,
) -> None:
    """ Recursive function to make object and children invisible.

    Optionally filter by a string in object name.

    """
    if obj is None:
        log.warning('Empty object given to toggle_hidden')
        return
    if hasattr(obj, 'hide_render') and hasattr(obj, 'hide_viewport'):
        if (filter_string is None) or (filter_string in obj.name):
            log.debug(f'Hiding object {obj.name}')
            bpy.data.objects[obj.name].select_set(True)
            bpy.data.objects[obj.name].hide_render = hidden
            bpy.data.objects[obj.name].hide_viewport = hidden
        else:
            log.debug(
                f'Object {obj.name} does not contain filter string {filter_string}')
    else:
        log.warning('Object does not have hide properties')
        return
    for child in obj.children:
        toggle_hidden(child, hidden=hidden, filter_string=filter_string)


def randomly_hide_within_collection(
    collections: List[bpy.types.Collection],
    chance_to_hide: float = 0.9,
) -> None:
    """ Randomly hide objects in a list of collections. """
    to_hide = []
    for obj in for_obj_in_collections(collections):
        if random.random() < chance_to_hide:
            to_hide.append(obj.name)
    # HACK: hide objects by name, this causes segfault
    # if done in the for loop above, due to some kind of
    # pass by reference vs by value shenaniganry going on
    # with blender python sitting on top of blender C
    for name in to_hide:
        bpy.data.objects[name].select_set(True)
        bpy.data.objects[name].hide_render = True
        bpy.data.objects[name].hide_viewport = True


def segment(
    obj: bpy.types.Object,
    name: str = 'default',
    color: Tuple[float] = None,
    as_category: bool = False,
    as_single: bool = False,
) -> None:
    """ Segment an object."""
    if color is None:
        color = zpy.color.random_color(output_style='frgb')
    obj.color = zpy.color.frgb_to_frgba(color)
    if as_category:
        obj.seg.category_name = name
        obj.seg.category_color = color
        seg_type = 'category'
    else:
        obj.seg.instance_name = name
        obj.seg.instance_color = color
        seg_type = 'instance'
    # Make sure object material is set up correctly with AOV nodes
    populate_vertex_colors(obj, zpy.color.frgb_to_frgba(color), seg_type)
    zpy.material.make_aov_material_output_node(obj=obj, style=seg_type)
    # Recursively add property to children objects
    if as_single:
        for child in obj.children:
            segment(
                obj=child,
                name=name,
                color=color,
                as_category=as_category,
                as_single=as_single,
            )


def populate_vertex_colors(
        obj: bpy.types.Object,
        color_rgba: Tuple[float],
        seg_type: str = 'instance',
) -> None:
    """Fill the given Vertex Color Layer with the color parameter values"""
    if not obj.type == 'MESH':
        log.warning(f'Object {obj.name} is not a mesh, has no vertices.')
        return
    select(obj)
    # Remove any existing vertex color data
    if len(obj.data.sculpt_vertex_colors):
        for vcol in obj.data.sculpt_vertex_colors.keys():
            if seg_type in vcol:
                obj.data.sculpt_vertex_colors.remove(
                    obj.data.sculpt_vertex_colors[seg_type])
    # Remove any existing vertex color data
    if len(obj.data.vertex_colors):
        for vcol in obj.data.vertex_colors.keys():
            if seg_type in vcol:
                obj.data.vertex_colors.remove(
                    obj.data.vertex_colors[seg_type])
    # Add new vertex color data
    obj.data.vertex_colors.new(name=seg_type)
    obj.data.sculpt_vertex_colors.new(name=seg_type)
    # Iterate through each vertex in the mesh
    for i, _ in enumerate(obj.data.vertices):
        obj.data.sculpt_vertex_colors[seg_type].data[i].color = color_rgba


def random_position_within_constraints(
    obj: bpy.types.Object
) -> None:
    """ Randomize position of object within constraints. """
    # Make sure object has constraints
    _constraints = obj.constraints.get('Limit Location', None)
    if _constraints is not None:
        obj.location.x = random.uniform(
            obj.constraints['Limit Location'].min_x,
            obj.constraints['Limit Location'].max_x,
        )
        obj.location.y = random.uniform(
            obj.constraints['Limit Location'].min_y,
            obj.constraints['Limit Location'].max_y,
        )
        obj.location.z = random.uniform(
            obj.constraints['Limit Location'].min_z,
            obj.constraints['Limit Location'].max_z,
        )


def copy(
    obj: bpy.types.Object,
    name: str = None,
    collection: bpy.types.Collection = None,
) -> bpy.types.Object:
    """ Create a copy of the object. """
    new_obj = bpy.data.objects.new(obj.name, obj.data)
    if name is not None:
        new_obj.name = name
    if collection is not None:
        collection.objects.link(new_obj)
    return new_obj


def translate(
    obj: bpy.types.Object,
    translation: Tuple[float] = (0, 0, 0),
) -> None:
    """ Translate an object (in blender units). """
    # select(obj)
    # bpy.ops.transform.translate(value=translation)
    # bpy.context.view_layer.update()
    mat_trans = mathutils.Matrix.Translation(translation)
    obj.matrix_world = mat_trans @ obj.matrix_world

def rotate(
    obj: bpy.types.Object,
    rotation: float = 0,
    axis: str = 'Z'
) -> None:
    """ Rotate an object (in radians) """
    # select(obj)
    # bpy.ops.transform.rotate(value=rotation, orient_axis=axis)
    # bpy.context.view_layer.update()
    mat_rot = mathutils.Matrix.Rotation(rotation, 4, axis)
    obj.matrix_world = mat_rot @ obj.matrix_world


def scale(
    obj: bpy.types.Object,
    scale: Tuple[float] = (1.0, 1.0, 1.0)
) -> None:
    """ Scale an object """
    # select(obj)
    # bpy.ops.transform.resize(value=scale)
    # bpy.context.view_layer.update()
    mag = scale[0] + scale[1] + scale[2]
    norm_vector = (scale[0] / mag, scale[1] / mag, scale[2] / mag)
    mat_scale = mathutils.Matrix.Scale(mag / 3.0, 4, norm_vector)
    obj.matrix_world = mat_scale @ obj.matrix_world


def jitter(
    obj: bpy.types.Object,
    translate_range: Tuple[Tuple[float]] = (
        (-0.05, 0.05),
        (-0.05, 0.05),
        (-0.05, 0.05),
    ),
    rotate_range: Tuple[Tuple[float]] = (
        (-0.05, 0.05),
        (-0.05, 0.05),
        (-0.05, 0.05),
    ),
    scale_range: Tuple[Tuple[float]] = (
        (1.0, 1.0),
        (1.0, 1.0),
        (1.0, 1.0),
    ),
) -> None:
    """ Apply random scale (blender units) and rotation (radians) to object """
    translate(obj,
              translation=(
                  random.uniform(translate_range[0][0], translate_range[0][1]),
                  random.uniform(translate_range[1][0], translate_range[1][1]),
                  random.uniform(translate_range[2][0], translate_range[2][1]),
              ))
    rotate(obj,
           rotation=random.uniform(rotate_range[0][0], rotate_range[0][1]),
           axis='X',
           )
    rotate(obj,
           rotation=random.uniform(rotate_range[1][0], rotate_range[1][1]),
           axis='Y',
           )
    rotate(obj,
           rotation=random.uniform(rotate_range[2][0], rotate_range[2][1]),
           axis='Z',
           )
    scale(obj,
          scale=(
              random.uniform(scale_range[0][0], scale_range[0][1]),
              random.uniform(scale_range[1][0], scale_range[1][1]),
              random.uniform(scale_range[2][0], scale_range[2][1]),
          ))
    bpy.context.view_layer.update()


_SAVED_POSES = {}


def save_pose(obj: bpy.types.Object, pose_name: str) -> None:
    """ Save a pose (rot and pos) to dict. """
    log.info(f'Saving pose {pose_name} based on object {obj.name}')
    _SAVED_POSES[pose_name] = obj.matrix_world.copy()


def restore_pose(obj: bpy.types.Object, pose_name: str) -> None:
    """ Restore an object to a position. """
    log.info(f'Restoring pose {pose_name} to object {obj.name}')
    obj.matrix_world = _SAVED_POSES[pose_name]
