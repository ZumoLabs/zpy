"""
    Blender Addons require a special __init__ file.
"""

import importlib
import logging
import sys
from pathlib import Path

log = logging.getLogger('zpy-addon')

bl_info = {
    "name": "Zpy Addon",
    "author": "Zumo Labs",
    "version": (1, 0),
    # TODO: Must be kept up to date with $BLENDER_VERSION in README.
    "blender": (2, 90, 0),
    "location": "View3D > Add > Mesh > Segmentium", # TODO: 
    "description": "Synthetic data creation tools for Blender.",
    "warning": "",
    "doc_url": "", # TODO: Link to Github README?
    "category": "Object",
}

if "bpy" in locals():
    from . import segment
    from . import render
    from . import export
    import zpy
    importlib.reload(segment)
    importlib.reload(render)
    importlib.reload(zpy)
    from zpy import blender
    from zpy import color
    from zpy import file
    from zpy import material
    from zpy import render
    from zpy import image
    # HACK: Reset the random colors on import
    zpy.color.reset()
else:
    import bpy
    import zpy
    from . import segment
    from . import render
    from . import export

classes = (
    # Properties
    segment.CategoryProperties,
    segment.SegmentableProperties,
    # Object operators
    segment.SegmentInstanceSingle,
    segment.SegmentInstanceMany,
    segment.ResetCategory,
    segment.ResetInstance,
    # Scene operators
    segment.VisualizeInstance,
    segment.VisualizeCategory,
    segment.CategoriesFromText,
    segment.CategoriesFromZUMOJSON,
    render.StepOperator,
    render.OpenOutputDirOperator,
    render.CleanOutputDirOperator,
    export.ExportOperator,
    export.OpenExportDirOperator,
    export.CleanUpDirOperator,
    # Panels
    segment.Panel,
    render.RenderPanel,
    export.ExportPanel,
)


def register():
    """ Register any classes and properties. """
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            log.warning(f'Exception when registering {cls.__name__}: {e}')
    segment.registerObjectProperties()
    segment.registerSceneProperties()
    render.registerSceneProperties()
    export.registerSceneProperties()


def unregister():
    """ Unregister any classes and properties. """
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            log.warning(f'Exception when un-registering {cls.__name__}: {e}')


if __name__ == "__main__":
    register()
