"""
    Blender Addons require a special __init__ file.
"""
import importlib
import logging

import bpy

log = logging.getLogger(__name__)

try:
    import zpy
except ModuleNotFoundError:
    log.warn('Could not find required pip packages.')
    install_pip_depenencies()
    import zpy

bl_info = {
    "name": "zpy",
    "author": "Zumo Labs",
    "version": (1, 0),
    # TODO: Keep up to date with $BLENDER_VERSION in README.
    "blender": (2, 91, 0),
    "location": "View3D > Properties > zpy",
    "description": "Synthetic data creation tools for Blender.",
    "warning": "",
    "doc_url": "https://github.com/ZumoLabs/zpy/blob/main/README.md",
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


def install_pip_depenencies():
    """ Install pip dependencies required by zpy addon."""
    log.info('Installing zpy and it\'s pip dendencies.')
    
    import subprocess
    import sys
    # TODO: METHOD 1
    # Install zpy and it's dependencies with setup.py
    subprocess.call([sys.executable,"setup.py","install", "--user"])

    # TODO: METHOD 2
    # Requirements files contains pip modules
    with open('requirements.txt') as f:
        required = f.read().splitlines()
    # Update pip and install required pip modules
    subprocess.call([sys.executable,"-m","pip", "install", "--upgrade","pip"])
    for pip_module in required:
        log.info(f'Installing pip module {pip_module}')
        subprocess.call([sys.executable,"-m","pip", "install", pip_module])


if __name__ == "__main__":
    register()
