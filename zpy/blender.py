"""
    Blender utilities.
"""
import inspect
import logging
import random
import time
from functools import wraps
from pathlib import Path
from typing import Dict, List, Union

import bpy
import gin
import mathutils
import numpy as np

import zpy

log = logging.getLogger(__name__)


def use_gpu(
    compute_device_type="CUDA",
    use_cpu=True,
) -> None:
    """Choose the rendering devices for rendering.

    The hybrid render device options (GPU+CPU) are possible for CUDA and OPTIX

    Args:
        compute_device_type (str, optional): One of [NONE, CUDA, OPTIX, OPENCL]. Defaults to 'CUDA'.
        use_cpu (bool, optional): Use CPU with compute device. Defaults to True.

    Raises:
        RuntimeError: Compute device is not a valid choice.
    """
    C = bpy.context
    preferences = bpy.context.preferences
    cycles_preferences = preferences.addons["cycles"].preferences
    compute_devices = [d[0] for d in cycles_preferences.get_device_types(C)]
    if compute_device_type not in compute_devices:
        raise RuntimeError("Non-existing device type")
    else:
        cycles_preferences.compute_device_type = compute_device_type
        devices = cycles_preferences.get_devices_for_type(compute_device_type)
        if len(devices) > 0:
            for c in devices:
                c.use = True
                if c.type == "CPU":
                    c.use = use_cpu
                log.info(f"Using devices {c} {c.type} {c.use}")

    C.scene.cycles.device = "GPU"
    log.info(f"Using gpu type:{compute_device_type} cpu:{use_cpu}")


@gin.configurable
def set_seed(
    seed: int = 0,
) -> None:
    """Set the random seed (sets the python and numpy seed).

    Args:
        seed (int, optional): Integer seed. Defaults to 0.
    """
    if log.getEffectiveLevel() == logging.DEBUG:
        # When debugging you want to run into errors related
        # to specific permutations of the random variables, so
        # you need to vary the seed to run into them.
        seed = random.randint(1, 100)
    log.info(f"Setting random seed to {seed}")
    random.seed(seed)
    np.random.seed(seed)
    mathutils.noise.seed_set(seed)


@gin.configurable
def step(
    num_steps: int = 3,
    framerate: int = 1,
    start_frame: int = 1,
    refresh_ui: bool = False,
) -> int:
    """Steps the sim forward (Blender frames).

    Args:
        num_steps (int, optional): Number of steps to take before the yield stops. Defaults to 16.
        framerate (int, optional): How many Blender frames to move forward in each step. Defaults to 0.
        start_frame (int, optional): Blender frame to start on. Defaults to 1.
        refresh_ui (bool, optional): Refresh the Blender UI on every step. Defaults to False.

    Returns:
        int: step id

    Yields:
        Iterator[int]: Step id
    """
    assert num_steps is not None, "Invalid num_steps"
    assert num_steps > 0, "Invalid num_steps"
    scene = zpy.blender.verify_blender_scene()
    step_idx = 0
    if framerate > 0:
        start = scene.frame_start
        stop = scene.frame_end
        log.info(f"Animation enabled. Min frames: {start}. Max frames: {stop}")
    while step_idx < num_steps:
        zpy.logging.linebreaker_log("step")
        log.info(f"Simulation step {step_idx + 1} of {num_steps}.")
        start_time = time.time()
        if framerate > 0:
            current_frame = start_frame + step_idx * framerate
            scene.frame_set(current_frame)
            log.info(f"Animation frame {scene.frame_current}")
        yield step_idx
        step_idx += 1
        duration = time.time() - start_time
        log.info(f"Simulation step took {duration}s to complete.")
        # TODO: This call is not needed in headless instances, makes loop faster
        if refresh_ui:
            refresh_blender_ui()


@gin.configurable
def verify_view_layer(
    view_layer_name: str = "View Layer",
) -> bpy.types.ViewLayer:
    """Get and set the view layer in Blender.

    Args:
        view_layer_name (str, optional): Name for View Layer. Defaults to 'View Layer'.

    Returns:
        bpy.types.ViewLayer: View Layer that will be used at runtime.
    """
    scene = zpy.blender.verify_blender_scene()
    view_layer = scene.view_layers.get(view_layer_name, None)
    if view_layer is None:
        log.debug(f"Could not find view layer {view_layer_name}")
        # Default behavior is to use first view layer
        view_layer = scene.view_layers[0]
    log.debug(f"Setting view layer to {view_layer.name}")
    bpy.context.window.view_layer = view_layer
    return view_layer


@gin.configurable
def verify_blender_scene(
    blender_scene_name: str = "Scene",
) -> bpy.types.Scene:
    """Get and set the scene in Blender.

    Args:
        blender_scene_name (str, optional): Name for Scene. Defaults to 'Scene'.

    Returns:
        bpy.types.Scene: Scene that will be used at runtime.
    """
    scene = bpy.data.scenes.get(blender_scene_name, None)
    if scene is None:
        log.debug(f"Could not find scene {blender_scene_name}")
        # Default behavior is to use the first scene
        scene = bpy.data.scenes[0]
    log.debug(f"Setting scene to {scene.name}")
    bpy.context.window.scene = scene
    return scene


def parse_config(
    text_name: str = "config",
) -> None:
    """Parses the gin config text in Blender.

    Args:
        text_name (str, optional): Name of the config text. Defaults to 'config'.
    """
    _text = bpy.data.texts.get(text_name, None)
    if _text is None:
        log.warning(f"Could not find {text_name} in texts.")
        return
    log.info(f"Loading gin config {text_name}")
    gin.enter_interactive_mode()
    with gin.unlock_config():
        gin.parse_config(_text.as_string())
        gin.finalize()


def save_and_revert(_func):
    """Decorator for saving blenderfile before execution, and
        reverting after execution.

    Args:
        _func (callable): function to be decorated.

    Returns:
        [callable]: Wrapped function.
    """

    @wraps(_func)
    def wrapped_func(*args, **kwargs) -> None:
        log.info("Saving the sim.")
        bpy.ops.wm.save_mainfile()
        try:
            _func(*args, **kwargs)
        except Exception as e:
            log.error(f"Executing {_func.__name__} failed with exception {e}")
            raise e
        finally:
            log.info("Reverting sim to previous savepoint.")
            bpy.ops.wm.revert_mainfile()

    return wrapped_func


def load_text_from_file(
    path: Union[Path, str],
    text_name: str = "",
    open_text: bool = False,
) -> None:
    """Load a file into Blender's internal text UI.

    Args:
        path (Union[Path, str]): Filesystem path.
        text_name (str, optional): Name of Blender text to write to.
    """
    path = zpy.files.verify_path(path)
    if bpy.data.texts.get(text_name, None) is None:
        _text = bpy.data.texts.load(str(path), internal=True)
        _text.name = text_name
    else:
        bpy.data.texts[text_name].from_string(path.read_text())
    if open_text:
        for area in bpy.context.screen.areas:
            if area.type == "TEXT_EDITOR":
                area.spaces[0].text = bpy.data.texts[text_name]


@gin.configurable
def connect_addon(
    name: str = "zpy_addon", addon_dir: Union[Path, str] = "$BLENDERADDONS"
) -> None:
    """Connects a Blender Addon.

    Args:
        name (str, optional): Name of Addon. Defaults to 'zpy_addon'.
        addon_dir (Union[Path, str], optional): Directory of addons. Defaults to '$BLENDERADDONS'.
    """
    log.debug(f"Connecting Addon {name}.")
    path = f"$BLENDERADDONS/{name}/__init__.py"
    path = zpy.files.verify_path(path, make=False)
    bpy.ops.preferences.addon_install(filepath=str(path))
    bpy.ops.preferences.addon_enable(module=name)


@gin.configurable
def connect_debugger_vscode(
    timeout: int = 3,
) -> None:
    """Connects to a VSCode debugger.

    https://github.com/AlansCodeLog/blender-debugger-for-vscode

    Args:
        timeout (int, optional): Seconds to connect before timeout. Defaults to 3.
    """
    if log.getEffectiveLevel() == logging.DEBUG:
        log.debug("Starting VSCode debugger in Blender.")
        connect_addon("blender-debugger-for-vscode")
        bpy.ops.debug.connect_debugger_vscode()
        for sec in range(timeout):
            log.debug(f"You have {timeout - sec} seconds to connect!")
            time.sleep(1)


def save_debug_blenderfile(
    path: Union[Path, str] = None,
) -> None:
    """Saves an intermediate blenderfile for debugging purposes.

    Args:
        path (Union[Path, str], optional): Output directory path.
    """
    if path is None:
        path = zpy.files.default_temp_path() / "_debug.blend"
    path = zpy.files.verify_path(path, make=False)
    log.debug(f"Saving intermediate blenderfile to {path}")
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=False, copy=True)


def refresh_blender_ui() -> None:
    """Refresh the Blender UI.

    Does not work on headless instances.
    """
    log.debug("Refreshing Blender UI.")
    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
    view_layer = zpy.blender.verify_view_layer()
    view_layer.update()


def load_sim(
    path: Union[Path, str],
    auto_execute_scripts: bool = True,
) -> None:
    """Load a sim from a path to a *.blend file.

    Args:
        path (Union[Path, str]): Path to .blend file.
        auto_execute_scripts (bool, optional): Whether to allow auto execution of scripts. Defaults to True.
    """
    # HACK: Clear out scene of cameras and lights
    clear_scene(["CAMERA", "LIGHT"])
    path = zpy.files.verify_path(path, make=False)
    log.debug(f"Loading sim from {str(path)}.")
    with bpy.data.libraries.load(str(path)) as (data_from, data_to):
        for attr in dir(data_to):
            setattr(data_to, attr, getattr(data_from, attr))
    # HACK: Delete current empty scene
    bpy.ops.scene.delete()
    # HACK: Delete extra workspaces that are created e.g. 'Animation.001'
    _workspaces = [ws for ws in bpy.data.workspaces if ".0" in ws.name]
    bpy.data.batch_remove(ids=_workspaces)
    # Allow execution of scripts inside loaded sim
    if auto_execute_scripts:
        log.warning("Allowing .blend file to run scripts automatically")
        log.warning("   this is unsafe for untrusted files")
        bpy.context.preferences.filepaths.use_scripts_auto_execute = (
            auto_execute_scripts
        )


def clear_scene(
    to_clear: List = ["MESH"],
) -> None:
    """Cleans objects in a scene based on the object type.

    Args:
        to_clear (List, optional): List of object types to clean. Defaults to ["MESH"].
    """
    log.debug(f"Deleting all objects of type {to_clear}")
    for obj in bpy.data.objects:
        if obj.type in to_clear:
            bpy.data.objects.remove(obj)


def scene_information() -> Dict:
    """Returns information on the scene, such as the kwargs in the run text.

    Raises:
        ValueError: Lack of run text and issues with the run text.

    Returns:
        Dict: Sim information dictionary.
    """
    log.info("Collecting scene information")
    run_script = bpy.data.texts.get("run", None)
    if run_script is None:
        raise ValueError("No run script found in scene.")
    # HACK: Gin is confused by the as_module() call
    gin.enter_interactive_mode()
    run_script_module = bpy.data.texts["run"].as_module()
    scene_doc = inspect.getdoc(run_script_module)

    run_function = None
    for name, value in inspect.getmembers(run_script_module):
        if name == "run":
            run_function = value
    if run_function is None:
        raise ValueError("No run() function found in run script.")
    if not inspect.isfunction(run_function):
        raise ValueError("run() is not a function in run script.")

    run_kwargs = []
    for param in inspect.signature(run_function).parameters.values():
        _kwarg = {}
        _kwarg["name"] = param.name
        _kwarg["type"] = str(param.annotation)
        _kwarg["default"] = param.default
        run_kwargs.append(_kwarg)

    scene = zpy.blender.verify_blender_scene()
    _ = {
        "name": scene.zpy_sim_name,
        "version": scene.zpy_sim_version,
        "description": scene_doc,
        "run_kwargs": run_kwargs,
        "export_date": time.strftime("%m%d%Y_%H%M_%S"),
        "zpy_version": zpy.__version__,
        "zpy_path": zpy.__file__,
        "blender_version": ".".join([str(_) for _ in bpy.app.version]),
    }
    log.info(f"{_}")
    return _
