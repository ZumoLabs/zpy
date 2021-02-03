"""
    KDTree utilities for Blender Python.
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


@gin.configurable
def random_points_in_bounded_3dgauss(
    x_mu: float,
    x_sigma: float,
    x_bounds: Tuple[float],
    y_mu: float,
    y_sigma: float,
    y_bounds: Tuple[float],
    z_mu: float,
    z_sigma: float,
    z_bounds: Tuple[float],
    num_points: int = 20,
    min_distance: float = 0.5,
    max_tries: int = None,
) -> List(mathutils.Vector):
    """ Randomly sample N points from 3D Gaussian into a kdtree. """
    points = []
    kd = mathutils.kdtree.KDTree(num_points)
    if max_tries is None:
        max_tries = num_points
    tries = 0
    while tries < max_tries:
        tries += 1
        sampled_point = (
            max(min(random.gauss(x_mu, x_sigma), x_bounds[1]), x_bounds[0]),
            max(min(random.gauss(y_mu, y_sigma), y_bounds[1]), y_bounds[0]),
            max(min(random.gauss(z_mu, z_sigma), z_bounds[1]), z_bounds[0]),
        )
        _, _, dist = kd.find(sampled_point)
        if dist <= min_distance:
            kd.insert(sampled_point, len(points))
            kd.balance()
            points.append(mathutils.Vector(sampled_point))
            if len(points) == num_points:
                break
    return points


def kdtree_from_collection(collections: List[bpy.types.Collection]) -> mathutils.kdtree.KDTree:
    """ Creates a KDTree of vertices from a collection of objects. """
    # First get the size of the objects (number of vertices)
    size = 0
    for obj in zpy.object.for_obj_in_collections(collections):
        size += len(obj.data.vertices)
    # Then add them to a tree object
    kd = mathutils.kdtree.KDTree(size)
    insert_idx = 0
    for obj in zpy.object.for_obj_in_collections(collections):
        for v in obj.data.vertices:
            world_coordinate_v = obj.matrix_world @ v.co
            kd.insert(world_coordinate_v, insert_idx)
            insert_idx += 1
    # Balancing is the most expensive operation
    kd.balance()
    return kd


@gin.configurable
def floor_occupancy(
    kdtree: mathutils.kdtree.KDTree,
    x_bounds: Tuple[float],
    y_bounds: Tuple[float],
    z_height: float = 0.0,
    num_points: int = 20,
) -> float:
    """ Get occupancy percentage for floor (XY plane). """
    log.info(f'Calculating floor occupancy ....')
    # TODO: This can definitely be vectorized better
    x_space, x_step = np.linspace(*x_bounds, num=num_points, retstep=True)
    y_space, y_step = np.linspace(*y_bounds, num=num_points, retstep=True)
    occupancy_grid = np.zeros((num_points, num_points))
    for x_idx, x in enumerate(x_space):
        for y_idx, y in enumerate(y_space):
            x = float(x)
            y = float(y)
            closest_point = kdtree.find((x, y, z_height))[0]
            if (closest_point.x > (x - x_step)) and \
                    (closest_point.x < (x + x_step)):
                if (closest_point.y > (y - y_step)) and \
                        (closest_point.y < (y + y_step)):
                    occupancy_grid[x_idx][y_idx] = 1.0
    log.info(f'... Done.')
    log.debug(f'Floor occupancy grid: {str(occupancy_grid)}')
    return float(np.mean(occupancy_grid.copy()))


@gin.configurable
def volume_occupancy(
    kdtree: mathutils.kdtree.KDTree,
    x_bounds: Tuple[float],
    y_bounds: Tuple[float],
    z_bounds: Tuple[float],
    num_points: int = 20,
) -> float:
    """ Get occupancy percentage for volume. """
    log.info(f'Calculating volume occupancy ....')
    # TODO: This can definitely be vectorized better
    x_space, x_step = np.linspace(*x_bounds, num=num_points, retstep=True)
    y_space, y_step = np.linspace(*y_bounds, num=num_points, retstep=True)
    z_space, z_step = np.linspace(*z_bounds, num=num_points, retstep=True)
    occupancy_grid = np.zeros((num_points, num_points, num_points))
    for x_idx, x in enumerate(x_space):
        for y_idx, y in enumerate(y_space):
            for z_idx, z in enumerate(z_space):
                x = float(x)
                y = float(y)
                z = float(z)
                closest_point = kdtree.find((x, y, z))[0]
                if (closest_point.x > (x - x_step)) and \
                        (closest_point.x < (x + x_step)):
                    if (closest_point.y > (y - y_step)) and \
                            (closest_point.y < (y + y_step)):
                        if (closest_point.z > (z - z_step)) and \
                                (closest_point.z < (z + z_step)):
                            occupancy_grid[x_idx][y_idx][z_idx] = 1.0
    log.info(f'... Done.')
    log.debug(f'Volume occupancy grid: {str(occupancy_grid)}')
    return float(np.mean(occupancy_grid.copy()))
