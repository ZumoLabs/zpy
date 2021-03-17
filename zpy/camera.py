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


def verify(
    camera: Union[bpy.types.Object, bpy.types.Camera, str],
    check_none=True,
) -> bpy.types.Camera:
    """ Return camera given name or typed object.

    Args:
        camera (Union[bpy.types.Object, bpy.types.Camera, str]): Camera object (or it's name)
        check_none (bool, optional): Raise error if object does not exist. Defaults to True.

    Raises:
        ValueError: Object does not exist.

    Returns:
        bpy.types.Camera: Camera object.
    """
    if isinstance(camera, str):
        camera = bpy.data.cameras.get(camera)
    if check_none and camera is None:
        raise ValueError(f'Could not find camera {camera}.')
    if camera is None:
        log.info(f'No camera chosen, using default scene camera \"{camera}\".')
        scene = zpy.blender.verify_blender_scene()
        camera = scene.camera
    return camera


def look_at(
    obj: Union[bpy.types.Object, str],
    location: Union[Tuple[float], mathutils.Vector],
    roll: float = 0,
) -> None:
    """ Rotate obj to look at target.

    Based on: https://blender.stackexchange.com/a/5220/12947

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name) that does the looking (usually a camera)
        location (Union[Tuple[float], mathutils.Vector]): Location (3-tuple or Vector) to be looked at.
        roll (float, optional): The angle of rotation about the axis from obj to target in radians. Defaults to 0.
    """
    obj = zpy.objects.verify(obj)
    if not isinstance(location, mathutils.Vector):
        location = mathutils.Vector(location)
    loc = obj.location
    # direction points from the object to the target
    direction = location - obj.location
    quat = direction.to_track_quat('-Z', 'Y')
    quat = quat.to_matrix().to_4x4()
    # convert roll from radians to degrees
    roll_matrix = mathutils.Matrix.Rotation(roll, 4, 'Z')
    # remember the current location, since assigning to obj.matrix_world changes it
    loc = loc.to_tuple()
    obj.matrix_world = quat @ roll_matrix
    obj.location = loc


@gin.configurable
def camera_xyz(
    location: Union[Tuple[float], mathutils.Vector],
    camera: Union[bpy.types.Object, bpy.types.Camera, str] = None,
    fisheye_lens: bool = False,
) -> Tuple[float]:
    """ Get pixel coordinates of point in camera space.

    - (0, 0) is the bottom left of the camera frame.
    - (1, 1) is the top right of the camera frame.
    - Values outside 0-1 are also supported.
    - A negative ‘z’ value means the point is behind the camera.

    Args:
        location (mathutils.Vector): Location (3-tuple or Vector) of point in 3D space.
        camera (Union[bpy.types.Object, bpy.types.Camera, str]): Camera in which pixel space exists.
        fisheye_lens (bool, optional): Whether to use fisheye distortion. Defaults to False.

    Returns:
        Tuple[float]: Pixel coordinates of location.
    """
    camera = zpy.camera.verify(camera)
    if not isinstance(location, mathutils.Vector):
        location = mathutils.Vector(location)
    scene = zpy.blender.verify_blender_scene()
    point = bpy_extras.object_utils.world_to_camera_view(
        scene, camera, location)
    # TODO: The z point here is incorrect?
    log.debug(F'Point {point}')
    if point[2] < 0:
        log.debug('Point is behind camera')

    # Fix the point based on camera distortion
    if fisheye_lens:
        log.debug('Correcting for fisheye distortion')

        # HACK: There should be a better place to put this
        bpy.data.cameras[0].lens_unit = 'FOV'
        bpy.data.cameras[0].lens = 18.

        # https://blender.stackexchange.com/questions/40702/how-can-i-get-the-projection-matrix-of-a-panoramic-camera-with-a-fisheye-equisol?noredirect=1&lq=1
        # Note this assumes 180 degree FOV
        cam = bpy.data.cameras[camera.name]
        f = cam.lens
        w = cam.sensor_width
        h = cam.sensor_height

        p = camera.matrix_world.inverted() @ location
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


def is_child_hit(
    obj: Union[bpy.types.Object, str],
    hit_obj: Union[bpy.types.Object, str],
) -> bool:
    """ Recursive function to check if a child object is the hit object.

    Args:
        obj (Union[bpy.types.Object, str]): Scene object (or it's name) that might contain a hit child.
        hit_obj (Union[bpy.types.Object, str]): Scene object (or it's name) that was hit

    Returns:
        bool: If the hit object is a child object.
    """
    obj = zpy.objects.verify(obj)
    hit_obj = zpy.objects.verify(hit_obj)
    if obj == hit_obj:
        return True
    else:
        for child in obj.children:
            if is_child_hit(child, hit_obj):
                return True
        return False


def is_visible(
    location: Union[Tuple[float], mathutils.Vector],
    obj_to_hit: Union[bpy.types.Object, str],
    camera: Union[bpy.types.Object, bpy.types.Camera, str] = None,
) -> bool:
    """ Cast a ray to determine if object is visible from camera.

    Args:
        location (Union[Tuple[float], mathutils.Vector]): Location to shoot out ray towards.
        obj_to_hit (Union[bpy.types.Object, str]): Object that should be hit by ray.
        camera (Union[bpy.types.Object, bpy.types.Camera, str]): Camera where ray originates from.

    Returns:
        bool: Whether the casted ray has hit the object.
    """
    camera = zpy.camera.verify(camera)
    obj_to_hit = zpy.objects.verify(obj_to_hit)
    if not isinstance(location, mathutils.Vector):
        location = mathutils.Vector(location)
    view_layer = zpy.blender.verify_view_layer()
    scene = zpy.blender.verify_blender_scene()
    result = scene.ray_cast(depsgraph=view_layer.depsgraph,
                            origin=camera.location,
                            direction=(location - camera.location))
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
    location: Union[Tuple[float], mathutils.Vector],
    camera: Union[bpy.types.Object, bpy.types.Camera, str] = None,
    epsilon: float = 0.05,
) -> bool:
    """ Is a location visible from a camera (within some epsilon).

    Args:
        location (Union[Tuple[float], mathutils.Vector]): Location that is visible or not.
        camera (Union[bpy.types.Object, bpy.types.Camera, str]): Camera that wants to see the location.
        epsilon (float, optional): How far outside the view box the point is allowed to be. Defaults to 0.05.

    Returns:
        bool: Whether the location is visible.
    """
    camera = zpy.camera.verify(camera)
    if not isinstance(location, mathutils.Vector):
        location = mathutils.Vector(location)
    x, y, z = camera_xyz(location, camera=camera)
    if z < 0:
        return False
    if x < (0-epsilon) or x > (1 + epsilon):
        return False
    if y < (0-epsilon) or y > (1 + epsilon):
        return False
    return True


@gin.configurable
def camera_xyv(
    location: Union[Tuple[float], mathutils.Vector],
    obj: Union[bpy.types.Object, str],
    camera: Union[bpy.types.Object, bpy.types.Camera, str] = None,
    width: int = 640,
    height: int = 480,
) -> Tuple[int]:
    """ Get camera image xyv coordinates of point in scene.

    Keypoint coordinates (x, y) are measured from the top left
    image corner (and are 0-indexed). Coordinates are rounded
    to the nearest pixel to reduce file size. Visibility (v):

        v=0: not labeled (in which case x=y=0)
        v=1: labeled but not visible
        v=2: labeled and visible

    Args:
        location (Union[Tuple[float], mathutils.Vector]): Location (3-tuple or Vector) of point in 3D space.
        obj (Union[bpy.types.Object, str]): Scene object (or it's name) to check for visibility.
        camera (Union[bpy.types.Object, bpy.types.Camera, str]): Camera in which pixel space exists.
        width (int, optional): Width of image. Defaults to 640.
        height (int, optional): Height of image. Defaults to 480.

    Returns:
        Tuple[int]: (X, Y, V)
    """
    camera = zpy.camera.verify(camera)
    obj = zpy.objects.verify(obj)
    if not isinstance(location, mathutils.Vector):
        location = mathutils.Vector(location)
    x, y, z = camera_xyz(location, camera=camera)
    # visibility
    v = 2
    if x < 0 or y < 0 or z < 0:
        v = 1
    if not is_visible(location, obj_to_hit=obj, camera=camera):
        v = 1
    # bottom-left to top-left
    y = 1 - y
    # float (0, 1) to pixel int (0, pixel size)
    x = int(x * width)
    y = int(y * height)
    log.debug(f'(x, y, v) {(x, y, v)}')
    return x, y, v
