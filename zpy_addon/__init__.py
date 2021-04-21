"""
    Blender Addons require a special __init__ file.
"""
import importlib
import logging
import subprocess
import sys
from pathlib import Path

import bpy

log = logging.getLogger(__name__)

bl_info = {
    "name": "zpy",
    "author": "Zumo Labs",
    # TODO: Keep up to date with $ZPY_VERSION
    "version": (1, 0, 0),
    # TODO: Keep up to date with $BLENDER_VERSION
    "blender": (2, 92, 0),
    "location": "View3D > Properties > zpy",
    "description": "Synthetic data creation tools for Blender.",
    "warning": "",
    "doc_url": "https://github.com/ZumoLabs/zpy/tree/main/README.md",
    "category": "3D View",
}


def install_pip_depenencies():
    """ Install pip dependencies required by zpy addon."""
    try:
        log.info('Installing zpy and dependencies...')
        # Upgrade pip with Blender's python
        pip_install = [sys.executable, "-m", "pip", "install"]
        subprocess.run(pip_install + ["--upgrade", "pip"], check=True)
        # Install zpy through PyPI into Blender's python site-package dir
        pkg_path = Path(sys.executable).parent.parent / \
            'lib' / 'site-packages' / 'zpy'
        subprocess.run(pip_install + ['zpy-zumo', '--target', str(pkg_path)],
                       check=True)
    except Exception as e:
        log.warning(f'Could not install ZPY and dependencies: {e}')


try:
    import zpy
except ModuleNotFoundError as e:
    log.exception('No zpy module found, please follow developer ' +
                  'install instructions at https://github.com/ZumoLabs/zpy#install')
    # TODO: Automatic installation of pip dependencies
    #       waiting on https://developer.blender.org/T71420
    # install_pip_depenencies()
    # import zpy

if "bpy" in locals():
    log.warning('Reloading zpy_addon files.')
    from . import export_panel
    from . import output_panel
    from . import execute_panel
    from . import script_panel
    from . import segment_panel
    importlib.reload(export_panel)
    importlib.reload(output_panel)
    importlib.reload(execute_panel)
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
    output_panel.OpenOutputDirOperator,
    output_panel.CleanOutputDirOperator,
    execute_panel.RenderOperator,
    execute_panel.RunOperator,
    export_panel.ExportOperator,
    export_panel.OpenExportDirOperator,
    export_panel.CleanUpDirOperator,
    script_panel.LoadGinConfigOperator,
    script_panel.PushGinConfigOperator,
    script_panel.LoadRunpyOperator,
    script_panel.PushRunpyOperator,
    script_panel.LoadTemplatesOperator,
    # Panels
    output_panel.SCENE_PT_OutputPanel,
    execute_panel.SCENE_PT_ExecutePanel,
    segment_panel.SCENE_PT_SegmentPanel,
    script_panel.SCENE_PT_ScriptPanel,
    export_panel.SCENE_PT_ExportPanel,
    # Menus
    script_panel.TEXT_PT_LoadRunPyTemplateOperator,
    script_panel.TEXT_PT_LoadGinConfigTemplateOperator,
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
    output_panel.registerSceneProperties()
    export_panel.registerSceneProperties()
    script_panel.registerSceneProperties()
    # Script templates
    bpy.types.TEXT_MT_templates_py.append(script_panel.script_template_menu)
    if "use_sculpt_vertex_colors" in dir(bpy.context.preferences.experimental):
        bpy.context.preferences.experimental.use_sculpt_vertex_colors = True



def unregister():
    """ Unregister any classes and properties. """
    for cls in classes:
        try:
            log.info(f'Un-registering class {cls.__name__}')
            bpy.utils.unregister_class(cls)
        except Exception as e:
            log.warning(f'Exception when un-registering {cls.__name__}: {e}')
    # Script templates
    bpy.types.TEXT_MT_templates_py.remove(script_panel.script_template_menu)


if __name__ == "__main__":
    register()
