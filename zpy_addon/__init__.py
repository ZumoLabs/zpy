"""
    Blender Addons require a special __init__ file.
"""
import importlib
import logging
import subprocess
import sys
from pathlib import Path
import shutil

import bpy

log = logging.getLogger(__name__)


def install_pip_depenencies():
    """ Install pip dependencies required by zpy addon."""
    log.info('Installing zpy and it\'s pip dendencies.')
    try:
        log.info('Installing zpy and dependencies...')
        # Requirements files contains pip modules
        requirements_path = Path(__file__).parent / 'requirements.txt'
        with open(requirements_path) as f:
            required = f.read().splitlines()
        # Update pip and install required pip modules
        subprocess.run([sys.executable, "-m", "pip",
                        "install", "--upgrade", "pip", "--user"], check=True)
        for pip_module in required:
            log.info(f'Installing pip module {pip_module}')
            subprocess.run([sys.executable, "-m", "pip",
                            "install", pip_module, "--user"], check=True)
        # Copy ZPY into Blender python's site packages
        zpy_path = Path(__file__).parent / 'zpy'
        package_path = Path(sys.executable).parent.parent / \
            'lib' / 'site-packages' / 'zpy'
        shutil.copytree(zpy_path, package_path)
        return
    except Exception as e:
        log.warning(f'Could not install ZPY and dependencies: {e}')


try:
    import zpy
except ModuleNotFoundError:
    log.warn('Could not find required pip packages.')
    install_pip_depenencies()

bl_info = {
    "name": "zpy",
    "author": "Zumo Labs",
    # TODO: Keep up to date with $ZPY_VERSION
    "version": (1, 0, 0),
    # TODO: Keep up to date with $BLENDER_VERSION
    "blender": (2, 91, 0),
    "location": "View3D > Properties > zpy",
    "description": "Synthetic data creation tools for Blender.",
    "warning": "",
    "doc_url": "https://github.com/ZumoLabs/zpy/tree/main/README.md",
    "category": "3D View",
}

if "bpy" in locals():
    log.warning('Reloading zpy_addon files.')
    from . import export_panel
    from . import render_panel
    from . import script_panel
    from . import segment_panel
    importlib.reload(export_panel)
    importlib.reload(render_panel)
    importlib.reload(script_panel)
    importlib.reload(segment_panel)
    from . import zpy
    importlib.reload(zpy)

classes = (
    # Properties
    segment_panel.CategoryProperties,
    segment_panel.SegmentableProperties,
    # Object operators
    segment_panel.SegmentInstanceSingle,
    segment_panel.SegmentInstanceMany,
    segment_panel.ResetSegData,
    # Scene operators
    segment_panel.VisualizeInstance,
    segment_panel.VisualizeCategory,
    segment_panel.CategoriesFromText,
    segment_panel.CategoriesFromZUMOJSON,
    render_panel.RenderOperator,
    render_panel.OpenOutputDirOperator,
    render_panel.CleanOutputDirOperator,
    export_panel.ExportOperator,
    export_panel.OpenExportDirOperator,
    export_panel.CleanUpDirOperator,
    script_panel.LoadGinConfigOperator,
    script_panel.PushGinConfigOperator,
    script_panel.LoadRunpyOperator,
    script_panel.PushRunpyOperator,
    script_panel.RunOperator,
    # Panels
    segment_panel.SegmentPanel,
    render_panel.RenderPanel,
    script_panel.ScriptPanel,
    export_panel.ExportPanel,
)


def register():
    """ Register any classes and properties. """
    for cls in classes:
        try:
            log.info(f'Registering class {cls.__name__}')
            bpy.utils.register_class(cls)
        except Exception as e:
            log.warning(f'Exception when registering {cls.__name__}: {e}')
    segment_panel.registerObjectProperties()
    segment_panel.registerSceneProperties()
    render_panel.registerSceneProperties()
    export_panel.registerSceneProperties()
    script_panel.registerSceneProperties()


def unregister():
    """ Unregister any classes and properties. """
    for cls in classes:
        try:
            log.info(f'Un-registering class {cls.__name__}')
            bpy.utils.unregister_class(cls)
        except Exception as e:
            log.warning(f'Exception when un-registering {cls.__name__}: {e}')


if __name__ == "__main__":
    register()
