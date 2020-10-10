"""
    Utilities for Blender Python.
"""
import logging
import math
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple, Union

import numpy as np
import zpy

import bpy
import bpy_extras
import gin
import mathutils

DEMO_STEP_MAX = 5

log = logging.getLogger(__name__)


def use_gpu() -> None:
    """ Use GPU for rendering. """
    devices = list(
        bpy.context.preferences.addons['cycles'].preferences.devices)
    log.debug(f'Devices available {devices}')
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'CUDA'
    devices = prefs.get_devices()
    for device in devices[0]:
        device.use = True
    log.debug(f'Devices available {devices}')


@gin.configurable
def set_seed(seed: int = 0) -> None:
    """ Set the random seed. """
    log.info(f'Setting random seed to {seed}')
    if log.getEffectiveLevel() == logging.DEBUG:
        # When debugging you want to run into errors related
        # to specific permutations of the random variables, so
        # you need to vary the seed to run into them.
        seed = random.randint(1, 100)
        log.debug(f'Choosing a random random seed of {seed}')
    random.seed(seed)
    np.random.seed(seed)


@gin.configurable
def step(num_steps: int = 16,
         demo: bool = False,
         framerate: int = 0,
         start_frame: int = 1,
         refresh_ui: bool = False,
         ) -> int:
    """ Step logic helper for the scene. """
    assert num_steps is not None, 'Invalid num_steps'
    assert num_steps > 0, 'Invalid num_steps'
    if demo:
        num_steps = min(num_steps, DEMO_STEP_MAX)
    step_idx = 0
    if framerate > 0:
        start = bpy.context.scene.frame_start
        stop = bpy.context.scene.frame_end
        log.info(f'Animation enabled. Min frames: {start}. Max frames: {stop}')
    while step_idx < num_steps:
        log.info(f'-----------------------------------------')
        log.info(f'                   STEP                  ')
        log.info(f'-----------------------------------------')
        log.info(f'Simulation step {step_idx} of {num_steps}.')
        start_time = time.time()
        if framerate > 0:
            current_frame = start_frame + step_idx * framerate
            bpy.context.scene.frame_set(current_frame)
            log.info(f'Animation frame {bpy.context.scene.frame_current}')
        # # Update the step_idx for all RandomEvent and Animator instances
        # RandomEvent.step_idx = step_idx
        yield step_idx
        step_idx += 1
        duration = time.time() - start_time
        log.info(f'Simulation step took {duration}s to complete.')
        # TODO: This call is not needed in headless instances, makes loop faster
        if refresh_ui:
            refresh_blender_ui()


def connect_debugger_vscode(timeout: int = 3) -> None:
    """ Connects to a VSCode debugger.

    Based on:

    https://github.com/AlansCodeLog/blender-debugger-for-vscode

    """
    if log.getEffectiveLevel() == logging.DEBUG:
        log.debug('Starting VSCode debugger in Blender.')
        path = '$BLENDERADDONS/blender-debugger-for-vscode/__init__.py'
        path = zpy.file.verify_path(path, make=False)
        bpy.ops.preferences.addon_install(filepath=str(path))
        bpy.ops.preferences.addon_enable(module='blender-debugger-for-vscode')
        bpy.ops.debug.connect_debugger_vscode()
        for sec in range(timeout):
            log.debug(f'You have {timeout - sec} seconds to connect!')
            time.sleep(1)


def parse_config(config_name: str = 'config') -> None:
    """ Load gin config for scene """
    config_text = bpy.data.texts.get(config_name, None)
    if config_text is None:
        log.warning(f'Could not find config {config_name} in texts.')
        return
    log.info(f'Loading gin config {config_name}')
    with gin.unlock_config():
        gin.parse_config(config_text.as_string())
        gin.finalize()


def connect_addon(name: str = 'zpy_addon') -> None:
    """ Connects a Blender AddOn. """
    log.debug(f'Connecting Addon {name}.')
    path = f'$BLENDERADDONS/{name}/__init__.py'
    path = zpy.file.verify_path(path, make=False)
    bpy.ops.preferences.addon_install(filepath=str(path))
    bpy.ops.preferences.addon_enable(module=name)


def output_intermediate_scene(path: Union[str, Path] = '/tmp/blender-debug-scene-tmp.blend') -> None:
    """ Output intermediate saved scene. """
    path = zpy.file.verify_path(path, make=False)
    log.debug(f'Saving intermediate scene to {path}')
    bpy.ops.wm.save_as_mainfile(filepath=str(path))


def refresh_blender_ui() -> None:
    """ Refresh blender in the middle of a script.

    Does not work on headless instances.
    """
    log.debug(f'Refreshing Blender UI.')
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    bpy.context.view_layer.update()


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


def load_scene(path: Union[str, Path]) -> None:
    """ Load a scene from a *.blend file. """
    # HACK: Clear out scene of cameras and lights
    clear_scene(['CAMERA', 'LIGHT'])
    path = zpy.file.verify_path(path, make=False)
    log.debug(f'Loading scene from {str(path)}.')
    with bpy.data.libraries.load(str(path)) as (data_from, data_to):
        for attr in dir(data_to):
            setattr(data_to, attr, getattr(data_from, attr))
    # HACK: Delete current empty scene
    bpy.ops.scene.delete()
    # HACK: Delete extra workspaces that are created e.g. 'Animation.001'
    _workspaces = [ws for ws in bpy.data.workspaces if '.0' in ws.name]
    bpy.data.batch_remove(ids=_workspaces)


def clear_scene(to_clear: List = ["MESH"]) -> None:
    """ Empty out the scene. """
    log.debug('Deleting all mesh objects in the scene.')
    for obj in bpy.data.objects:
        if obj.type in to_clear:
            bpy.data.objects.remove(obj)


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
        log.warning('Point is behind camera')

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
    result = scene.ray_cast(view_layer=bpy.context.window.view_layer,
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


@gin.configurable
def camera_xyv(
    loc: mathutils.Vector,
    obj: bpy.types.Object,
    camera: bpy.types.Camera = None,
    image_width: int = 480,
    image_height: int = 640,
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
