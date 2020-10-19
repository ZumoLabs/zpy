"""
    Script loading/running panel and functions.
"""
import hashlib
import importlib
import json
import logging
import os
import random
from pathlib import Path
import math

import bpy
import mathutils
from bpy.types import Operator

log = logging.getLogger(__name__)

if "bpy" in locals():
    import zpy
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
    import zpy


def registerSceneProperties():
    """ Properties applied to scenes."""
    bpy.types.Scene.zpy_gin_config_path = bpy.props.StringProperty(
        name='',
        description="Path to a gin config file.",
        default='',
        subtype='FILE_PATH',
        update=_load_gin_config,
    )
    bpy.types.Scene.zpy_runpy_path = bpy.props.StringProperty(
        name='',
        description="Path to run.py file",
        default='',
        subtype='FILE_PATH',
        update=_load_runpy,
    )


def _load_gin_config(self, context) -> None:
    """ Load gin config from file. """
    bpy.ops.scene.zpy_load_gin_config()


def _load_runpy(self, context) -> None:
    """ Load run.py from file. """
    bpy.ops.scene.zpy_load_runpy()


class CommitOperator(Operator):
    """ Write out run and config texts to file outside .blend file. """
    bl_idname = "scene.zpy_commit"
    bl_label = "Commit"
    bl_description = "Write out run and config texts to file outside .blend file."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        return {'FINISHED'}


class RunOperator(Operator):
    """ Launch the run script in Blender's texts. """
    bl_idname = "scene.zpy_run"
    bl_label = "Run"
    bl_description = "Launch the run script in Blender's texts."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        zpy.blender.parse_config(LoadGinConfigOperator.DEFAULT_TEXT_NAME)
        zpy.blender.run_text(LoadRunpyOperator.DEFAULT_TEXT_NAME)
        return {'FINISHED'}


class LoadGinConfigOperator(bpy.types.Operator):
    """ Load gin config from file. """
    bl_idname = "scene.zpy_load_gin_config"
    bl_label = "Load gin config from file."
    bl_description = "Load gin config from file."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    # Default name of the texts in Blender when loading
    DEFAULT_TEXT_NAME = "config"

    def execute(self, context):
        zpy.blender.load_text_from_file(
            bpy.path.abspath(context.scene.zpy_gin_config_path),
            text_name=self.DEFAULT_TEXT_NAME)
        return {'FINISHED'}

class PushGinConfigOperator(bpy.types.Operator):
    """ Push gin config to file. """
    bl_idname = "scene.zpy_push_gin_config"
    bl_label = "Push gin config to file."
    bl_description = "Push gin config to file."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        _text = bpy.data.texts[LoadGinConfigOperator.DEFAULT_TEXT_NAME].as_string()
        with open(bpy.path.abspath(context.scene.zpy_gin_config_path), 'w') as _file:
            _file.write(_text)
        return {'FINISHED'}

class LoadRunpyOperator(bpy.types.Operator):
    """ Load run.py from file. """
    bl_idname = "scene.zpy_load_runpy"
    bl_label = "Load run.py from file."
    bl_description = "Load run.py from file."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    # Default name of the texts in Blender when loading
    DEFAULT_TEXT_NAME = "run"

    def execute(self, context):
        zpy.blender.load_text_from_file(
            bpy.path.abspath(context.scene.zpy_runpy_path),
            text_name=self.DEFAULT_TEXT_NAME)
        return {'FINISHED'}

class PushRunpyOperator(bpy.types.Operator):
    """ Push run.py to file. """
    bl_idname = "scene.zpy_push_runpy"
    bl_label = "Push run.py to file."
    bl_description = "Push run.py to file."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _text = bpy.data.texts[LoadRunpyOperator.DEFAULT_TEXT_NAME].as_string()
        with open(bpy.path.abspath(context.scene.zpy_runpy_path), 'w') as _file:
            _file.write(_text)
        return {'FINISHED'}

class ScriptPanel(bpy.types.Panel):
    """ UI for the addon that is visible in Blender. """
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Script"
    bl_category = "ZumoLabs"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator(
            'scene.zpy_run',
            text='Run',
            icon='TRIA_RIGHT',
        )
        row = layout.row()
        row.label(text="Run.py Path")
        row = layout.row()
        row.prop(scene, "zpy_runpy_path")
        row = layout.row()
        row.operator(
            'scene.zpy_load_runpy',
            text='Pull',
            icon='IMPORT',
        )
        row.operator(
            'scene.zpy_push_runpy',
            text='Push',
            icon='EXPORT',
        )
        row = layout.row()
        row.label(text="Gin Config Path")
        row = layout.row()
        row.prop(scene, "zpy_gin_config_path")
        row = layout.row()
        row.operator(
            'scene.zpy_load_gin_config',
            text='Pull',
            icon='IMPORT',
        )
        row.operator(
            'scene.zpy_push_gin_config',
            text='Push',
            icon='EXPORT',
        )
