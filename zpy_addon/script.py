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
        name='Output path',
        description="Path to a gin config file.",
        default='',
        subtype='FILE_PATH',
    )
    bpy.types.Scene.zpy_runpy_path = bpy.props.StringProperty(
        name='Output path',
        description="Path to run.py file",
        default='',
        subtype='FILE_PATH',
    )


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
    DEFAULT_TEXT_NAME = 'config'

    def execute(self, context):
        zpy.blender.load_text_from_file(
            context.scene.zpy_gin_config_path,
            self.DEFAULT_TEXT_NAME)
        return {'FINISHED'}


class LoadRunpyOperator(bpy.types.Operator):
    """ Load run.py from file. """
    bl_idname = "scene.zpy_load_runpy"
    bl_label = "Load run.py from file."
    bl_description = "Load run.py from file."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    # Default name of the texts in Blender when loading
    DEFAULT_TEXT_NAME = 'run'

    def execute(self, context):
        zpy.blender.load_text_from_file(
            context.scene.zpy_runpy_path,
            self.DEFAULT_TEXT_NAME)
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
        row.prop(scene, "zpy_gin_config_path")
        row = layout.row()
        row.operator(
            'scene.zpy_load_gin_config',
            text='Load Config',
            icon='FILEBROWSER',
        )
        row = layout.row()
        row.prop(scene, "zpy_runpy_path")
        row = layout.row()
        row.operator(
            'scene.zpy_load_runpy',
            text='Load Runpy',
            icon='FILEBROWSER',
        )
        row = layout.row()
        row.operator(
            'scene.zpy_run',
            text='Run',
            icon='FILE_IMAGE',
        )
