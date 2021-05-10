"""
    KDTree utilities for Blender Python.
"""
import logging
from typing import List, Tuple

import bpy
import gin
import mathutils
import numpy as np

import zpy

log = logging.getLogger(__name__)


def kdtree_from_collection(
    collections: List[bpy.types.Collection],
) -> mathutils.kdtree.KDTree:
    """Creates a KDTree of vertices from a collection of objects."""
    # First get the size of the objects (number of vertices)
    size = 0
    for obj in zpy.objects.for_obj_in_collections(collections):
        size += len(obj.data.vertices)
    # Then add them to a tree object
    kd = mathutils.kdtree.KDTree(size)
    insert_idx = 0
    for obj in zpy.objects.for_obj_in_collections(collections):
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
    num_voxels: int = 100,
) -> float:
    """Get occupancy percentage for floor (XY plane)."""
    log.info("Calculating floor occupancy ....")
    x_side_length = abs(x_bounds[1] - x_bounds[0])
    y_side_length = abs(y_bounds[1] - y_bounds[0])
    # Number of voxels determines number of points in each dimmension
    voxel_cube_side_length = ((x_side_length * y_side_length) / num_voxels) ** (1 / 2)
    num_points_x = x_side_length / voxel_cube_side_length
    num_points_y = y_side_length / voxel_cube_side_length
    # TODO: This can definitely be vectorized better
    x_space, x_step = np.linspace(*x_bounds, num=int(num_points_x), retstep=True)
    y_space, y_step = np.linspace(*y_bounds, num=int(num_points_y), retstep=True)
    occupancy_grid = np.zeros((int(num_points_x), int(num_points_y)))
    for x_idx, x in enumerate(x_space):
        for y_idx, y in enumerate(y_space):
            x = float(x)
            y = float(y)
            closest_point = kdtree.find((x, y, z_height))[0]
            if (closest_point.x > (x - x_step)) and (closest_point.x < (x + x_step)):
                if (closest_point.y > (y - y_step)) and (
                    closest_point.y < (y + y_step)
                ):
                    occupancy_grid[x_idx][y_idx] = 1.0
    log.info("... Done.")
    log.debug(f"Floor occupancy grid: {str(occupancy_grid)}")
    return float(np.mean(occupancy_grid.copy()))


@gin.configurable
def volume_occupancy(
    kdtree: mathutils.kdtree.KDTree,
    x_bounds: Tuple[float],
    y_bounds: Tuple[float],
    z_bounds: Tuple[float],
    num_voxels: int = 100,
) -> float:
    """Get occupancy percentage for volume."""
    log.info("Calculating volume occupancy ....")
    x_side_length = abs(x_bounds[1] - x_bounds[0])
    y_side_length = abs(y_bounds[1] - y_bounds[0])
    z_side_length = abs(z_bounds[1] - z_bounds[0])
    # Number of voxels determines number of points in each dimmension
    voxel_cube_side_length = (
        (x_side_length * y_side_length * z_side_length) / num_voxels
    ) ** (1 / 3)
    num_points_x = x_side_length / voxel_cube_side_length
    num_points_y = y_side_length / voxel_cube_side_length
    num_points_z = z_side_length / voxel_cube_side_length
    # TODO: This can definitely be vectorized better
    x_space, x_step = np.linspace(*x_bounds, num=int(num_points_x), retstep=True)
    y_space, y_step = np.linspace(*y_bounds, num=int(num_points_y), retstep=True)
    z_space, z_step = np.linspace(*z_bounds, num=int(num_points_z), retstep=True)
    occupancy_grid = np.zeros((int(num_points_x), int(num_points_y), int(num_points_z)))
    for x_idx, x in enumerate(x_space):
        for y_idx, y in enumerate(y_space):
            for z_idx, z in enumerate(z_space):
                x = float(x)
                y = float(y)
                z = float(z)
                closest_point = kdtree.find((x, y, z))[0]
                if (closest_point.x > (x - x_step)) and (
                    closest_point.x < (x + x_step)
                ):
                    if (closest_point.y > (y - y_step)) and (
                        closest_point.y < (y + y_step)
                    ):
                        if (closest_point.z > (z - z_step)) and (
                            closest_point.z < (z + z_step)
                        ):
                            occupancy_grid[x_idx][y_idx][z_idx] = 1.0
    log.info("... Done.")
    log.debug(f"Volume occupancy grid: {str(occupancy_grid)}")
    return float(np.mean(occupancy_grid.copy()))
