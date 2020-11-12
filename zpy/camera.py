"""
    Camera utilities.
"""
import logging
import math
from pathlib import Path
from typing import Dict, List, Tuple, Union

import bpy
import bpy_extras
import gin
import mathutils

import zpy

log = logging.getLogger(__name__)


def look_at(obj: bpy.types.Object,
            target: Union[Tuple[float], mathutils.Vector],
            roll: float = 0) -> None:
    """
    Rotate obj to look at target

    :arg obj: the object to be rotated. Usually the camera
    :arg target: the location (3-tuple or Vector) to be looked at
    :arg roll: The angle of rotation about the axis from obj to target in degrees.

    Based on: https://blender.stackexchange.com/a/5220/12947 (ideasman42)
    """
    if not isinstance(target, mathutils.Vector):
        target = mathutils.Vector(target)
    loc = obj.location
    # direction points from the object to the target
    direction = target - obj.location
    quat = direction.to_track_quat('-Z', 'Y')
    # /usr/share/blender/scripts/addons/add_advanced_objects_menu/arrange_on_curve.py
    quat = quat.to_matrix().to_4x4()
    # convert roll from radians to degrees
    roll_matrix = mathutils.Matrix.Rotation(math.radians(roll), 4, 'Z')
    # remember the current location, since assigning to obj.matrix_world changes it
    loc = loc.to_tuple()
    obj.matrix_world = quat @ roll_matrix
    obj.location = loc


@gin.configurable
def camera_xyz(
    loc: mathutils.Vector,
    camera: bpy.types.Object = None,
    fisheye_lens: bool = False,
) -> Tuple[float]:
    """ Get camera image xy coordinates of point in scene.

    - (0, 0) is the bottom left of the camera frame.
    - (1, 1) is the top right of the camera frame.
    - Values outside 0-1 are also supported.
    - A negative ‘z’ value means the point is behind the camera.

    """
    scene = bpy.context.scene
    if camera is None:
        camera = scene.camera
    point = bpy_extras.object_utils.world_to_camera_view(scene, camera, loc)
    if point[2] < 0:
        log.debug('Point is behind camera')

    # Fix the point based on camera distortion
    if fisheye_lens:
        log.debug('Correcting for fisheye distortion')

        # HACK: There should be a better place to put this
        bpy.data.cameras[0].lens_unit = 'FOV'
        bpy.data.cameras[0].lens = 18.

        # Based on https://blender.stackexchange.com/questions/40702/how-can-i-get-the-projection-matrix-of-a-panoramic-camera-with-a-fisheye-equisol?noredirect=1&lq=1
        # Note this assumes 180 degree FOV
        cam = bpy.data.cameras[camera.name]
        f = cam.lens
        w = cam.sensor_width
        h = cam.sensor_height

        p = camera.matrix_world.inverted() @ loc
        p.normalize()

        # Calculate our angles
        phi = math.atan2(p.y, p.x)
        l = (p.x**2 + p.y**2)**(1/2)
        theta = math.asin(l)

        # Equisolid projection
        r = 2.0 * f * math.sin(theta / 2)

        u = r * math.cos(phi) / w + 0.5
        v = r * math.sin(phi) / h + 0.5

        # x = u * scene.render.resolution_x
        # y = v * scene.render.resolution_y
        # TODO: The value of point[2] here is not exactly correct ...
        return u, v, point[2]

    else:
        return point[0], point[1], point[2]


def is_child_hit(obj: bpy.types.Object, hit_obj: bpy.types.Object) -> bool:
    """ Recursive function to check if child is the hit object. """
    if obj == hit_obj:
        return True
    else:
        for child in obj.children:
            if is_child_hit(child, hit_obj):
                return True
        return False


@gin.configurable
def is_visible(
    loc: mathutils.Vector,
    obj_to_hit: bpy.types.Object,
    camera: bpy.types.Camera = None,
) -> bool:
    """ Cast a ray to determine if object is visible from camera. """
    scene = bpy.context.scene
    if camera is None:
        camera = scene.camera
    result = scene.ray_cast(depsgraph=bpy.context.view_layer.depsgraph,
                            origin=camera.location,
                            direction=(loc - camera.location))
    # Whether a hit occured
    is_hit = result[0]
    # Object hit by raycast
    hit_obj = result[4]
    if not is_hit:
        # Nothing was hit by the ray
        log.debug(f'No raycast hit from camera to {obj_to_hit.name}')
        return False
    if is_child_hit(obj_to_hit, hit_obj):
        # One of the children of the obj_to_hit was hit
        log.debug(f'Raycast hit from camera to {obj_to_hit.name}')
        return True
    return False


@gin.configurable
def is_in_view(
    loc: mathutils.Vector,
    camera: bpy.types.Camera = None,
    epsilon: float = 0.05,
) -> bool:
    """ Is a point visible to camera? Within some epsilon. """
    x, y, z = camera_xyz(loc, camera=camera)
    if z < 0:
        return False
    if x < (0-epsilon) or x > (1 + epsilon):
        return False
    if y < (0-epsilon) or y > (1 + epsilon):
        return False
    return True


@gin.configurable
def camera_xyv(
    loc: mathutils.Vector,
    obj: bpy.types.Object,
    camera: bpy.types.Camera = None,
    image_width: int = 640,
    image_height: int = 480,
) -> Tuple[int]:
    """ Get camera image xyv coordinates of point in scene.

    Keypoint coordinates (x, y) are measured from the top left
    image corner (and are 0-indexed). Coordinates are rounded
    to the nearest pixel to reduce file size. Visibility (v):

        v=0: not labeled (in which case x=y=0)
        v=1: labeled but not visible
        v=2: labeled and visible

    """
    x, y, z = camera_xyz(loc, camera=camera)
    # visibility
    v = 2
    if x < 0 or y < 0 or z < 0:
        v = 1
    if not is_visible(loc, obj_to_hit=obj, camera=camera):
        v = 1
    # bottom-left to top-left
    y = 1 - y
    # float (0, 1) to pixel int (0, pixel size)
    x = int(x * image_width)
    y = int(y * image_height)
    return x, y, v
