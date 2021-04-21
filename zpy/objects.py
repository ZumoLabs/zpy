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


def verify(
    obj: Union[bpy.types.Object, str],
    check_none=True,
) -> bpy.types.Object:
    """ Return object given name or Object type object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        check_none (bool, optional): Raise error if object does not exist. Defaults to True.

    Raises:
        ValueError: Object does not exist.

    Returns:
        bpy.types.Object: Scene object.
    """
    if isinstance(obj, str):
        obj = bpy.data.objects.get(obj)
    if check_none and obj is None:
        raise ValueError(f'Could not find object {obj}.')
    return obj


def load_blend_obj(
        name: str,
        path: Union[Path, str],
        link: bool = False,
) -> bpy.types.Object:
    """ Load object from blend file.

    Args:
        name (str): Name of object to be loaded.
        path (Union[Path, str]): Path to the blender file with the object.
        link (bool, optional): Whether to link object to scene. Defaults to False.

    Returns:
        bpy.types.Object: Scene object that was loaded in.
    """
    path = zpy.files.verify_path(path, make=False)
    scene = zpy.blender.verify_blender_scene()
    with bpy.data.libraries.load(str(path), link=link) as (data_from, data_to):
        for from_obj in data_from.objects:
            if from_obj.startswith(name):
                log.debug(f'Loading obj {from_obj} from {str(path)}.')
                data_to.objects.append(from_obj)
    # Copy objects over to the current scene
    for obj in data_to.objects:
        scene.collection.objects.link(obj)
    for texture_folder_name in ['Textures', 'textures', 'TEX']:
        texture_dir = path.parent / texture_folder_name
        if texture_dir.exists():
            bpy.ops.file.find_missing_files(directory=str(texture_dir))
            break
    return bpy.data.objects[name]


def select(
    obj: Union[bpy.types.Object, str],
) -> None:
    """ Select an object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
    """
    obj = verify(obj)
    view_layer = zpy.blender.verify_view_layer()
    # TODO: This sometimes does not work due to context issues
    log.debug(f'Selecting obj: {obj.name}')
    bpy.ops.object.select_all(action='DESELECT')
    view_layer.objects.active = obj
    bpy.data.objects[obj.name].select_set(True, view_layer=view_layer)


def delete_obj(
    obj: Union[bpy.types.Object, str],
) -> None:
    """ Delete an object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
    """
    obj = verify(obj)
    select(obj)
    log.debug(f'Removing obj: {obj.name}')
    # bpy.ops.object.delete()
    bpy.data.objects.remove(obj, do_unlink=True)


def delete_obj_context(
    obj: Union[bpy.types.Object, str],
) -> None:
    """ Alternative way to delete an object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
    """
    obj = verify(obj)
    log.debug(f'Removing obj: {obj.name}')
    context_remove = bpy.context.copy()
    context_remove['selected_objects'] = [obj]
    bpy.ops.object.delete(context_remove)


def empty_collection(
    collection: bpy.types.Collection = None,
    method: str = "data",
) -> None:
    """ Delete all objects in a collection

    Args:
        collection (bpy.types.Collection, optional): Optional collection to put new object inside of. Defaults to None.
        method (str, optional): Deletetion method, the values are data and context
    """
    if collection and  ( collection in list(bpy.data.collections)):
        if method == 'data':
            for obj in collection.all_objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        elif method == 'context':
            context_remove = bpy.context.copy()
            context_remove['selected_objects'] = collection.all_objects
            bpy.ops.object.delete(context_remove)


def is_inside(
    location: Union[Tuple[float], mathutils.Vector],
    obj: Union[bpy.types.Object, str],
) -> bool:
    """Is point inside a mesh.

    https://blender.stackexchange.com/questions/31693/how-to-find-if-a-point-is-inside-a-mesh

    Args:
        location (Union[Tuple[float], mathutils.Vector]): Location (3-tuple or Vector) of point in 3D space.
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)

    Returns:
        bool: Whether object is inside mesh.
    """
    if not isinstance(location, mathutils.Vector):
        location = mathutils.Vector(location)
    is_found, closest_point, normal, _ = obj.closest_point_on_mesh(location)
    if not is_found:
        return False
    p2 = closest_point - location
    v = p2.dot(normal)
    return not(v < 0.0)


def for_obj_in_selected_objs(context) -> bpy.types.Object:
    """ Safe iterable for selected objects.

    Yields:
        bpy.types.Object: Objects in selected objects.
    """
    zpy.blender.verify_view_layer()
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
    """ Yield objects in list of collection.

    Yields:
        bpy.types.Object: Object in collection.
    """
    for collection in collections:
        for obj in collection.all_objects:
            if obj.type == 'MESH':
                # This gives you direct access to data block
                yield bpy.data.objects[obj.name]


def toggle_hidden(
    obj: Union[bpy.types.Object, str],
    hidden: bool = True,
    filter_string: str = None,
) -> None:
    """ Recursive function to make object and children invisible.

    Optionally filter by a string in object name.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        hidden (bool, optional): Whether to hide or un-hide object. Defaults to True.
        filter_string (str, optional): Filter objects to hide based on name containing this string. Defaults to None.
    """
    obj = verify(obj)
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
    """ Randomly hide objects in a list of collections.

    Args:
        collections (List[bpy.types.Collection]): A scene collection.
        chance_to_hide (float, optional): Probability of hiding an object in the collection. Defaults to 0.9.
    """
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
    obj: Union[bpy.types.Object, str],
    name: str = 'default',
    color: Tuple[float] = None,
    as_category: bool = False,
    as_single: bool = False,
) -> None:
    """ Segment an object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        name (str, optional): Name of category or instance. Defaults to 'default'.
        color (Tuple[float], optional): Segmentation color. Defaults to None.
        as_category (bool, optional): Segment as a category, if false will segment as instance. Defaults to False.
        as_single (bool, optional): Segment all child objects as well. Defaults to False.
    """
    if "use_sculpt_vertex_colors" in dir(bpy.context.preferences.experimental):
        bpy.context.preferences.experimental.use_sculpt_vertex_colors = True
    obj = verify(obj)
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
    obj: Union[bpy.types.Object, str],
    color_rgba: Tuple[float],
    seg_type: str = 'instance',
) -> None:
    """ Fill the given Vertex Color Layer with the color parameter values.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        color_rgba (Tuple[float]): Segmentation color.
        seg_type (str, optional): Instance or Category segmentation. Defaults to 'instance'.
    """
    obj = verify(obj)
    if not obj.type == 'MESH':
        log.warning(f'Object {obj.name} is not a mesh, has no vertices.')
        return
    # TODO: Is this select needed?
    # select(obj)
    # Remove any existing vertex color data
    if len(obj.data.sculpt_vertex_colors):
        for vcol in obj.data.sculpt_vertex_colors.keys():
            if seg_type in vcol:
                obj.data.sculpt_vertex_colors.remove(
                    obj.data.sculpt_vertex_colors[seg_type])
    # Add new vertex color data
    obj.data.sculpt_vertex_colors.new(name=seg_type)
    # Iterate through each vertex in the mesh
    for i, _ in enumerate(obj.data.vertices):
        obj.data.sculpt_vertex_colors[seg_type].data[i].color = color_rgba


def random_position_within_constraints(
    obj: Union[bpy.types.Object, str],
) -> None:
    """ Randomize position of object within constraints.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
    """
    obj = verify(obj)
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


@gin.configurable
def copy(
    obj: Union[bpy.types.Object, str],
    name: str = None,
    collection: bpy.types.Collection = None,
    is_library_object: bool = False,
    is_copy: bool = True,
) -> bpy.types.Object:
    """ Create a copy of the object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        name (str, optional): New name for the copied object. Defaults to None.
        collection (bpy.types.Collection, optional): Optional collection to put new object inside of. Defaults to None.
        is_library_object (bool, optional): Whether object is part of a linked library. Defaults to False.
        is_copy (bool, optional): Make a deep copy of the mesh data block
    Returns:
        bpy.types.Object: The newly created scene object.
    """
    obj = verify(obj)
    obj_data=obj.data
    if is_copy:
        obj_data=obj.data.copy()
    new_obj = bpy.data.objects.new(obj.name, obj_data)
    if name is not None:
        new_obj.name = name
    if collection is not None:
        collection.objects.link(new_obj)
    else:
        # Add to scene collection if no collection given
        scene = zpy.blender.verify_blender_scene()
        scene.collection.objects.link(obj)
    # TODO: Library Overriding functions
    if is_library_object:
        log.warning(
            f'Making mesh and material data local for obj {new_obj.name}')
        new_obj.data.make_local()
        for i in range(len(new_obj.material_slots)):
            bpy.data.objects[new_obj.name].material_slots[i].material.make_local()
        # Original object reference is lost if local copies are made
        new_obj = bpy.data.objects[new_obj.name]
    return new_obj


def translate(
    obj: Union[bpy.types.Object, str],
    translation: Union[Tuple[float], mathutils.Vector] = (0, 0, 0),
    is_absolute: bool = False,
) -> None:
    """ Translate an object (in blender units).

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        translation (Union[Tuple[float], mathutils.Vector], optional): Translation vector (x, y, z). Defaults to (0, 0, 0).
        is_absolute: (bool, optional): The translation vector becomes the absolute world position

    """
    obj = verify(obj)
    log.debug(f'Translating object {obj.name} by {translation}')
    log.debug(f'Before - obj.matrix_world\n{obj.matrix_world}')
    if not isinstance(translation, mathutils.Vector):
        translation = mathutils.Vector(translation)
    if is_absolute:
        obj.location = translation
    else:
        obj.location = obj.location + translation
    log.debug(f'After - obj.matrix_world\n{obj.matrix_world}')


def rotate(
    obj: Union[bpy.types.Object, str],
    rotation: Union[Tuple[float], mathutils.Euler] = (0.0, 0.0, 0.0),
    axis_order: str = 'XYZ'
) -> None:
    """ Rotate the given object with Euler angles.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        rotation (Union[Tuple[float], mathutils.Euler]): Rotation values in radians
        axis_order (str, optional): Axis order of rotation
    """
    obj = verify(obj)
    view_layer = zpy.blender.verify_view_layer()
    select(obj)
    log.info(
        f'Rotating object {obj.name} by {rotation} radians in {axis_order}. ')
    log.debug(f'Before - obj.matrix_world\n{obj.matrix_world}')
    if not isinstance(rotation, mathutils.Euler):
        rotation = mathutils.Euler(rotation)
    new_rotation_mat = rotation.to_matrix() @ obj.rotation_euler.to_matrix()
    new_rotation = new_rotation_mat.to_euler(axis_order)
    obj.rotation_euler = mathutils.Euler(new_rotation, axis_order)
    view_layer.update()
    log.debug(f'After - obj.matrix_world\n{obj.matrix_world}')


def scale(
    obj: Union[bpy.types.Object, str],
    scale: Tuple[float] = (1.0, 1.0, 1.0)
) -> None:
    """ Scale an object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        scale (Tuple[float], optional): Scale for each axis (x, y, z). Defaults to (1.0, 1.0, 1.0).
    """
    obj = verify(obj)
    view_layer = zpy.blender.verify_view_layer()
    select(obj)
    log.info(f'Scaling object {obj.name} by {scale}')
    log.debug(f'Before - obj.matrix_world\n{obj.matrix_world}')
    bpy.ops.transform.resize(value=scale)
    view_layer.update()
    log.debug(f'After - obj.matrix_world\n{obj.matrix_world}')


def jitter_mesh(
    obj: Union[bpy.types.Object, str],
    scale: Tuple[float] = (0.01, 0.01, 0.01),
) -> None:
    """ Randomize the vertex coordinates of a mesh object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        scale (Tuple[float], optional): Scale for vertex offset in each axis (x, y, z). Defaults to (0.01, 0.01, 0.01).
    """
    obj = verify(obj)
    if not obj.type == 'MESH':
        log.warning('Jitter mesh requires object to be of type MESH')
        return
    for vertex in obj.data.vertices:
        offset = mathutils.Vector((
            random.uniform(-1.0, 1.0) * obj.dimensions.x * scale[0],
            random.uniform(-1.0, 1.0) * obj.dimensions.y * scale[1],
            random.uniform(-1.0, 1.0) * obj.dimensions.z * scale[2],
        ))
        vertex.co += offset


def jitter(
    obj: Union[bpy.types.Object, str],
    translate_range: Tuple[Tuple[float]] = (
        (0, 0),
        (0, 0),
        (0, 0),
    ),
    rotate_range: Tuple[Tuple[float]] = (
        (0, 0),
        (0, 0),
        (0, 0),
    ),
    scale_range: Tuple[Tuple[float]] = (
        (1.0, 1.0),
        (1.0, 1.0),
        (1.0, 1.0),
    ),
) -> None:
    """ Apply random scale (blender units) and rotation (radians) to object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        translate_range (Tuple[Tuple[float]], optional): (min, max) of uniform noise on translation in (x, y, z) axes. Defaults to ( (-0.05, 0.05), (-0.05, 0.05), (-0.05, 0.05), ).
        rotate_range (Tuple[Tuple[float]], optional): (min, max) of uniform noise on rotation in (x, y, z) axes. Defaults to ( (-0.05, 0.05), (-0.05, 0.05), (-0.05, 0.05), ).
        scale_range (Tuple[Tuple[float]], optional): (min, max) of uniform noise on scale in (x, y, z) axes. Defaults to ( (1.0, 1.0), (1.0, 1.0), (1.0, 1.0), ).
    """
    obj = verify(obj)
    translate(obj,
              translation=(
                  random.uniform(translate_range[0][0], translate_range[0][1]),
                  random.uniform(translate_range[1][0], translate_range[1][1]),
                  random.uniform(translate_range[2][0], translate_range[2][1]),
              ))
    rotate(obj,
           rotation=(
               random.uniform(rotate_range[0][0], rotate_range[0][1]),
               random.uniform(rotate_range[1][0], rotate_range[1][1]),
               random.uniform(rotate_range[2][0], rotate_range[2][1]),
           ))
    scale(obj,
          scale=(
              random.uniform(scale_range[0][0], scale_range[0][1]),
              random.uniform(scale_range[1][0], scale_range[1][1]),
              random.uniform(scale_range[2][0], scale_range[2][1]),
          ))


_SAVED_POSES = {}


def save_pose(
    obj: Union[bpy.types.Object, str],
    pose_name: str,
) -> None:
    """ Save a pose (rot and pos) to dict.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        pose_name (str): Name of saved pose (will be stored in internal SAVED_POSES dict)
    """
    obj = verify(obj)
    log.info(f'Saving pose {pose_name} based on object {obj.name}')
    _SAVED_POSES[pose_name] = obj.matrix_world.copy()


def restore_pose(
    obj: Union[bpy.types.Object, str],
    pose_name: str,
) -> None:
    """ Restore an object to a position.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name)
        pose_name (str): Name of saved pose (must be in internal SAVED_POSES dict)
    """
    obj = verify(obj)
    log.info(f'Restoring pose {pose_name} to object {obj.name}')
    obj.matrix_world = _SAVED_POSES[pose_name]
