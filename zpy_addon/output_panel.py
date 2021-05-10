"""
    Output panel and functions.
"""
import importlib
import logging

import bpy
import zpy
from bpy.types import Operator

log = logging.getLogger(__name__)

if "bpy" in locals():
    importlib.reload(zpy)


def registerSceneProperties():
    """Properties applied to scenes."""
    bpy.types.Scene.zpy_output_path = bpy.props.StringProperty(
        name="Output Path",
        description="Output path for rendered images, annotations, etc.",
        default=str(zpy.files.default_temp_path()),
        subtype="DIR_PATH",
    )


class CleanOutputDirOperator(bpy.types.Operator):
    """Clean up output dir."""

    bl_idname = "scene.zpy_cleanup_output_dir"
    bl_label = "Clean Output Dir"
    bl_description = "Clean output dir."
    bl_category = "ZPY"
    bl_options = {"REGISTER"}

    def execute(self, context):
        zpy.files.clean_dir(context.scene.zpy_output_path, keep_dir=True)
        return {"FINISHED"}


class OpenOutputDirOperator(Operator):
    """Open file browser at output dir."""

    bl_idname = "scene.zpy_open_output_dir"
    bl_label = "Open Output Dir"
    bl_description = "Open file browser at output dir."
    bl_category = "ZPY"
    bl_options = {"REGISTER"}

    def execute(self, context):
        zpy.files.open_folder_in_explorer(context.scene.zpy_output_path, make=True)
        return {"FINISHED"}


class SCENE_PT_OutputPanel(bpy.types.Panel):
    """UI for the addon that is visible in Blender."""

    bl_idname = "SCENE_PT_OutputPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Output Path"
    bl_category = "ZPY"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.prop(scene, "zpy_output_path", text="")
        row = layout.row()
        row.operator(
            "scene.zpy_open_output_dir",
            text="Open",
            icon="FILEBROWSER",
        )
        row.operator(
            "scene.zpy_cleanup_output_dir",
            text="Clean",
            icon="PACKAGE",
        )
