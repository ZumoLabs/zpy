"""
    Blender utilities.
"""
import inspect
import logging
import math
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple, Union

import bpy
import gin
import mathutils
import numpy as np

import zpy

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


def set_log_levels(level: str = None) -> None:
    """ Set logger levels for all zpy modules. """
    if level is None:
        log_level = logging.INFO
    elif level == 'info':
        log_level = logging.INFO
    elif level == 'debug':
        log_level = logging.DEBUG
    elif level == 'warning':
        log_level = logging.WARNING
    else:
        log.warning(f'Invalid log level {level}')
        return
    log.warning(f'Setting log level to {log_level}')
    for logger_name in ['zpy', 'zpy_addon', 'zpy.savers', 'bpy.zpy_addon']:
        logging.getLogger(logger_name).setLevel(log_level)


@gin.configurable
def step(
    num_steps: int = 16,
    framerate: int = 0,
    start_frame: int = 1,
    refresh_ui: bool = False,
) -> int:
    """ Step logic helper for the scene. """
    assert num_steps is not None, 'Invalid num_steps'
    assert num_steps > 0, 'Invalid num_steps'
    step_idx = 0
    if framerate > 0:
        start = bpy.context.scene.frame_start
        stop = bpy.context.scene.frame_end
        log.info(f'Animation enabled. Min frames: {start}. Max frames: {stop}')
    while step_idx < num_steps:
        log.info('-----------------------------------------')
        log.info('                   STEP                  ')
        log.info('-----------------------------------------')
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
        # TODO: Can we assume the user will properly set up this environment variable?
        path = '$BLENDERADDONS/blender-debugger-for-vscode/__init__.py'
        path = zpy.files.verify_path(path, make=False)
        bpy.ops.preferences.addon_install(filepath=str(path))
        bpy.ops.preferences.addon_enable(module='blender-debugger-for-vscode')
        bpy.ops.debug.connect_debugger_vscode()
        for sec in range(timeout):
            log.debug(f'You have {timeout - sec} seconds to connect!')
            time.sleep(1)


def parse_config(text_name: str = 'config') -> None:
    """ Load gin config for scene """
    _text = bpy.data.texts.get(text_name, None)
    if _text is None:
        log.warning(f'Could not find {text_name} in texts.')
        return
    log.info(f'Loading gin config {text_name}')
    gin.enter_interactive_mode()
    with gin.unlock_config():
        gin.parse_config(_text.as_string())
        gin.finalize()


def run_text(text_name: str = 'run') -> None:
    """ Run a text script in Blender. """
    _text = bpy.data.texts.get(text_name, None)
    if _text is None:
        log.warning(f'Could not find {text_name} in texts.')
        return
    _ctx = bpy.context.copy()
    _ctx['edit_text'] = _text
    bpy.ops.text.run_script(_ctx)


def connect_addon(name: str = 'zpy_addon') -> None:
    """ Connects a Blender AddOn. """
    log.debug(f'Connecting Addon {name}.')
    path = f'$BLENDERADDONS/{name}/__init__.py'
    path = zpy.files.verify_path(path, make=False)
    bpy.ops.preferences.addon_install(filepath=str(path))
    bpy.ops.preferences.addon_enable(module=name)


def output_intermediate_scene(path: Union[str, Path] = None) -> None:
    """ Output intermediate saved scene. """
    if path is None:
        path = zpy.files.default_temp_path() / 'blender-debug-scene-tmp.blend'
    path = zpy.files.verify_path(path, make=False)
    log.debug(f'Saving intermediate scene to {path}')
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=False, copy=True)


def refresh_blender_ui() -> None:
    """ Refresh blender in the middle of a script.

    Does not work on headless instances.
    """
    log.debug(f'Refreshing Blender UI.')
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    bpy.context.view_layer.update()


def load_scene(
    path: Union[str, Path],
    auto_execute_scripts : bool = True,
    ) -> None:
    """ Load a scene from a *.blend file. """
    # HACK: Clear out scene of cameras and lights
    clear_scene(['CAMERA', 'LIGHT'])
    path = zpy.files.verify_path(path, make=False)
    log.debug(f'Loading scene from {str(path)}.')
    with bpy.data.libraries.load(str(path)) as (data_from, data_to):
        for attr in dir(data_to):
            setattr(data_to, attr, getattr(data_from, attr))
    # HACK: Delete current empty scene
    bpy.ops.scene.delete()
    # HACK: Delete extra workspaces that are created e.g. 'Animation.001'
    _workspaces = [ws for ws in bpy.data.workspaces if '.0' in ws.name]
    bpy.data.batch_remove(ids=_workspaces)
    # Allow execution of scripts inside loaded scene
    if auto_execute_scripts:
        log.warning('Allowing .blend file to run scripts automatically')
        log.warning('   this is unsafe for blend files from an untrusted source')
        bpy.context.preferences.filepaths.use_scripts_auto_execute = auto_execute_scripts


def clear_scene(to_clear: List = ["MESH"]) -> None:
    """ Empty out the scene. """
    log.debug('Deleting all mesh objects in the scene.')
    for obj in bpy.data.objects:
        if obj.type in to_clear:
            bpy.data.objects.remove(obj)


def load_text_from_file(
    path: Union[str, Path],
    text_name: str = '',
) -> None:
    """ Load a file into Blender's internal text UI. """
    path = zpy.files.verify_path(path)
    if bpy.data.texts.get(text_name, None) is None:
        _text = bpy.data.texts.load(str(path), internal=True)
        _text.name = text_name
    else:
        bpy.data.texts[text_name].from_string(path.read_text())


def scene_information() -> Dict:
    """ Get the run() function kwargs. """
    log.info(f'Collecting scene information')
    run_script = bpy.data.texts.get('run', None)
    if run_script is None:
        raise ValueError('No run script found in scene.')
    # HACK: Gin is confused by the as_module() call
    gin.enter_interactive_mode()
    run_script_module = bpy.data.texts['run'].as_module()
    scene_doc = inspect.getdoc(run_script_module)

    run_function = None
    for name, value in inspect.getmembers(run_script_module):
        if name == 'run':
            run_function = value
    if run_function is None:
        raise ValueError('No run() function found in run script.')
    if not inspect.isfunction(run_function):
        raise ValueError('run() is not a function in run script.')

    run_kwargs = []
    for param in inspect.signature(run_function).parameters.values():
        _kwarg = {}
        _kwarg['name'] = param.name
        _kwarg['type'] = str(param.annotation)
        _kwarg['default'] = param.default
        run_kwargs.append(_kwarg)

    _ = {
        'name': bpy.context.scene.zpy_scene_name,
        'version': bpy.context.scene.zpy_scene_version,
        'description': scene_doc,
        'run_kwargs': run_kwargs,
        'export_date':  time.strftime("%m%d%Y_%H%M_%S"),
        'zpy_version': zpy.__version__,
        'zpy_path': zpy.__file__,
        'blender_version': '.'.join([str(_) for _ in bpy.app.version]),
    }
    log.info(f'{_}')
    return _


@gin.configurable
def load_hdri(
    path: Union[str, Path],
    scale: Tuple[float] = (1.0, 1.0, 1.0),
) -> None:
    """ Load an HDRI from path.

    Great source of HDRIs:

        https://hdrihaven.com/

    """
    log.info(f'Loading HDRI at {path}')
    path = zpy.files.verify_path(path, make=False)
    world = bpy.context.scene.world
    world.use_nodes = True
    out_node = world.node_tree.nodes.get('World Output', None)
    if out_node is None:
        out_node = world.node_tree.nodes.new('World Output')
    bg_node = world.node_tree.nodes.get('Background', None)
    if bg_node is None:
        bg_node = world.node_tree.nodes.new('Background')
    env_node = world.node_tree.nodes.get('Environment Texture', None)
    if env_node is None:
        env_node = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
    env_node.image = bpy.data.images.load(str(path))
    env_node.texture_mapping.scale = mathutils.Vector(scale)
    # env_node.texture_mapping.rotation = mathutils.Vector(
    #     (0,-math.radians(90), math.radians(180)))
    # world.node_tree.links.new(env_node.inputs[0], tex_node.outputs[4])
    world.node_tree.links.new(bg_node.inputs[0], env_node.outputs[0])
    world.node_tree.links.new(out_node.inputs[0], bg_node.outputs[0])


@gin.configurable
def random_hdri(
    asset_dir: Union[str, Path] = '$ASSETS/lib/hdris/hdri_maker_lib/04k_Library',
) -> Path:
    """ Generate a random HDRI from an asset path. """
    asset_directory = zpy.files.verify_path(
        asset_dir, make=False, check_dir=True)
    hdri_path = random.choice([x for x in asset_directory.iterdir() if x.is_file()])
    load_hdri(hdri_path)
    return hdri_path
