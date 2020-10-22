"""
    Object utilities for Blender Python.
"""
import inspect
import logging
import math
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple, Union

import bpy
import bpy_extras
import gin
import mathutils
import numpy as np

import zpy

log = logging.getLogger(__name__)


def load_blend_obj(name: str,
                   path: Union[str, Path],
                   link: bool = False) -> bpy.types.Object:
    """ Load object from blend file. """
    path = zpy.file.verify_path(path, make=False)
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


def delete_obj(name=str) -> None:
    """ Delete a human by name. """
    # TODO: Delete a human from the collections
    obj = bpy.data.collections.get(name)
    if obj is not None:
        bpy.context.active_object = obj
        bpy.ops.object.delete(confirm=False)
        log.debug(f'Removed obj: {name}')
    else:
        log.debug(f'Could not find obj: {name}')


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


def rotate_object(
    obj: bpy.types.Object,
    rotation_value: float = 0,
    rotation_axis: str = 'Z'
):
    """ rotate an object """
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.transform.rotate(value=rotation_value, orient_axis=rotation_axis)


def scale_object(
    obj: bpy.types.Object,
    scale: Tuple[float] = (1.0, 1.0, 1.0)
):
    """ scale an object """
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.transform.resize(value=scale)


def jitter_object(
    obj: bpy.types.Object,
    max_scale: float = 1.2,
    min_scale: float = 0.8,
    min_rotate: float = 0.0,
    max_rotate: float = 7.0
):
    """ apply random scale and rotation to object """
    random_rotation = random.uniform(min_rotate, max_rotate)
    rotate_object(obj, random_rotation)
    random_scale = (random.uniform(min_scale, max_scale),
                    random.uniform(min_scale, max_scale), 0)
    scale_object(obj, random_scale)
