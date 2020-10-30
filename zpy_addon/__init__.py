"""
    Blender Addons require a special __init__ file.
"""
import importlib
import logging

import bpy
import zpy

log = logging.getLogger(__name__)

bl_info = {
    "name": "zpy",
    "author": "Zumo Labs",
    "version": (1, 0),
    # TODO: Keep up to date with $BLENDER_VERSION in README.
    "blender": (2, 90, 0),
    "location": "View3D > Properties > zpy",
    "description": "Synthetic data creation tools for Blender.",
    "warning": "",
    "doc_url": "https://github.com/ZumoLabs/zpy/blob/main/README.md",
    "category": "3D View",
}

if "bpy" in locals():
    log.warning('Reloading zpy_addon files.')
    from . import export, render, script, segment
    importlib.reload(export)
    importlib.reload(render)
    importlib.reload(script)
    importlib.reload(segment)
    importlib.reload(zpy)

classes = (
    # Properties
    segment.CategoryProperties,
    segment.SegmentableProperties,
    # Object operators
    segment.SegmentInstanceSingle,
    segment.SegmentInstanceMany,
    segment.ResetSegData,
    # Scene operators
    segment.VisualizeInstance,
    segment.VisualizeCategory,
    segment.CategoriesFromText,
    segment.CategoriesFromZUMOJSON,
    render.RenderOperator,
    render.OpenOutputDirOperator,
    render.CleanOutputDirOperator,
    export.ExportOperator,
    export.OpenExportDirOperator,
    export.CleanUpDirOperator,
    script.LoadGinConfigOperator,
    script.PushGinConfigOperator,
    script.LoadRunpyOperator,
    script.PushRunpyOperator,
    script.RunOperator,
    # Panels
    segment.SegmentPanel,
    render.RenderPanel,
    script.ScriptPanel,
    export.ExportPanel,
)


def register():
    """ Register any classes and properties. """
    for cls in classes:
        try:
            log.info(f'Registering class {cls.__name__}')
            bpy.utils.register_class(cls)
        except Exception as e:
            log.warning(f'Exception when registering {cls.__name__}: {e}')
    segment.registerObjectProperties()
    segment.registerSceneProperties()
    render.registerSceneProperties()
    export.registerSceneProperties()
    script.registerSceneProperties()


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
