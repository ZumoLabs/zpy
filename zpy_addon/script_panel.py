"""
    Script loading/running panel and functions.
"""
import importlib
import logging
from pathlib import Path

import bpy
import zpy
from bpy.types import Operator

log = logging.getLogger(__name__)

if "bpy" in locals():
    importlib.reload(zpy)


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
    bpy.types.Scene.zpy_template_dir = bpy.props.StringProperty(
        name='',
        description='Path to script template directory.',
        default=str(zpy.blender.default_script_template_dir()),
        subtype='DIR_PATH',
    )


def _load_gin_config(self, context) -> None:
    """ Load gin config from file. """
    bpy.ops.scene.zpy_load_gin_config()


def _load_runpy(self, context) -> None:
    """ Load run.py from file. """
    bpy.ops.scene.zpy_load_runpy()


class LoadGinConfigOperator(bpy.types.Operator):
    """ Load gin config from file. """
    bl_idname = "scene.zpy_load_gin_config"
    bl_label = "Load gin config from file."
    bl_description = "Load gin config from file."
    bl_category = "ZPY"
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
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _text = bpy.data.texts[LoadGinConfigOperator.DEFAULT_TEXT_NAME].as_string(
        )
        with open(bpy.path.abspath(context.scene.zpy_gin_config_path), 'w') as _file:
            _file.write(_text)
        return {'FINISHED'}


class LoadRunpyOperator(bpy.types.Operator):
    """ Load run.py from file. """
    bl_idname = "scene.zpy_load_runpy"
    bl_label = "Load run.py from file."
    bl_description = "Load run.py from file."
    bl_category = "ZPY"
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
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _text = bpy.data.texts[LoadRunpyOperator.DEFAULT_TEXT_NAME].as_string()
        with open(bpy.path.abspath(context.scene.zpy_runpy_path), 'w') as _file:
            _file.write(_text)
        return {'FINISHED'}


class SCENE_PT_ScriptPanel(bpy.types.Panel):
    """ UI for the addon that is visible in Blender. """
    bl_idname = "SCENE_PT_ScriptPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Script"
    bl_category = "ZPY"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator(
            'scene.zpy_load_templates',
            text='Load Templates',
            icon='TEXT',
        )
        row = layout.row()
        row.label(text="Run.py Path")
        row = layout.row()
        row.prop(scene, "zpy_runpy_path", expand=True)
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


class LoadTemplatesOperator(bpy.types.Operator):
    """ Loads templates for run.py and gin config. """
    bl_idname = "scene.zpy_load_templates"
    bl_label = "Loads templates for run.py and gin config."
    bl_description = "Loads templates for run.py and gin config."
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.text.zpy_load_ginconfig_template()
        bpy.ops.text.zpy_load_runpy_template()
        return {'FINISHED'}


class TEXT_PT_LoadRunPyTemplateOperator(bpy.types.Operator):
    """ Opens the run.py template. """
    bl_idname = "text.zpy_load_runpy_template"
    bl_label = "Open zpy run.py template."

    def execute(self, context):
        template_dir = Path(bpy.path.abspath(context.scene.zpy_template_dir))
        template_path = template_dir / 'run.py'
        zpy.blender.load_text_from_file(
            template_path,
            text_name=LoadRunpyOperator.DEFAULT_TEXT_NAME,
            open_text=True,
        )
        return {'FINISHED'}


class TEXT_PT_LoadGinConfigTemplateOperator(bpy.types.Operator):
    """ Opens the gin config template. """
    bl_idname = "text.zpy_load_ginconfig_template"
    bl_label = "Open gin config template."

    def execute(self, context):
        template_dir = Path(bpy.path.abspath(context.scene.zpy_template_dir))
        template_path = template_dir / 'config.gin'
        zpy.blender.load_text_from_file(
            template_path,
            text_name=LoadGinConfigOperator.DEFAULT_TEXT_NAME,
            open_text=True,
        )
        return {'FINISHED'}


def script_template_menu(self, context):
    self.layout.separator()
    self.layout.operator(
        'text.zpy_load_runpy_template', text='(zpy) Run Script')
    self.layout.operator(
        'text.zpy_load_ginconfig_template', text='(zpy) Config Text')
