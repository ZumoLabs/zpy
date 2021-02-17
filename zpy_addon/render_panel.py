"""
    Rendering panel and functions.
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
    bpy.types.Scene.zpy_output_path = bpy.props.StringProperty(
        name='Output Path',
        description="Output path for rendered images, annotations, etc.",
        default=str(zpy.files.default_temp_path()),
        subtype='DIR_PATH',
    )


class RenderOperator(Operator):
    """ Render out single image (rgb, segmented, depth). """
    bl_idname = "scene.zpy_render"
    bl_label = "Render"
    bl_description = "Render out segmented images."
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        # TODO: Make sure scene is good to render?
        return True

    def execute(self, context):
        context.space_data.shading.color_type = 'OBJECT'

        # Image names
        rgb_image_name = zpy.files.make_rgb_image_name(0)
        cseg_image_name = zpy.files.make_cseg_image_name(0)
        iseg_image_name = zpy.files.make_iseg_image_name(0)
        depth_image_name = zpy.files.make_depth_image_name(0)

        # Output path
        output_path = Path(context.scene.zpy_output_path)

        # Save renders to file
        zpy.render.render_aov(
            rgb_path=output_path / rgb_image_name,
            iseg_path=output_path / iseg_image_name,
            cseg_path=output_path / cseg_image_name,
            depth_path=output_path / depth_image_name,
            width=640,
            height=480,
        )

        return {'FINISHED'}


class CleanOutputDirOperator(bpy.types.Operator):
    """ Clean up output dir. """
    bl_idname = "scene.zpy_cleanup_output_dir"
    bl_label = "Clean Output Dir"
    bl_description = "Clean output dir."
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    def execute(self, context):
        zpy.files.clean_dir(context.scene.zpy_output_path, keep_dir=True)
        return {'FINISHED'}


class OpenOutputDirOperator(Operator):
    """ Open file browser at output dir. """
    bl_idname = "scene.zpy_open_output_dir"
    bl_label = "Open Output Dir"
    bl_description = "Open file browser at output dir."
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    def execute(self, context):
        zpy.files.open_folder_in_explorer(
            context.scene.zpy_output_path, make=True)
        return {'FINISHED'}


class RenderPanel(bpy.types.Panel):
    """ UI for the addon that is visible in Blender. """
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Render"
    bl_category = "ZPY"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator(
            'scene.zpy_render',
            text='Render',
            icon='FILE_IMAGE',
        )
        row = layout.row()
        row.label(text="Output Path")
        row = layout.row()
        row.prop(scene, "zpy_output_path", text="")
        row = layout.row()
        row.operator(
            'scene.zpy_open_output_dir',
            text='Open',
            icon='FILEBROWSER',
        )
        row.operator(
            'scene.zpy_cleanup_output_dir',
            text='Clean',
            icon='PACKAGE',
        )
