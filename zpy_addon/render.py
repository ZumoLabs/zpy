"""
    Rendering panel and functions.
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
    bpy.types.Scene.zpy_output_path = bpy.props.StringProperty(
        name='Output Path',
        description="Output path for rendered images, annotations, etc.",
        default=str(zpy.file.default_temp_path()),
        subtype='DIR_PATH',
    )


class RenderOperator(Operator):
    """ Render out single image (rgb, segmented, depth). """
    bl_idname = "scene.zpy_render"
    bl_label = "Render"
    bl_description = "Render out segmented images."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        # TODO: Make sure scene is good to render?
        return True

    def execute(self, context):
        context.space_data.shading.color_type = 'OBJECT'

        # Image names
        rgb_image_name = zpy.file.make_rgb_image_name(0)
        cseg_image_name = zpy.file.make_cseg_image_name(0)
        iseg_image_name = zpy.file.make_iseg_image_name(0)
        depth_image_name = zpy.file.make_depth_image_name(0)

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
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        zpy.file.clean_dir(context.scene.zpy_output_path, keep_dir=True)
        return {'FINISHED'}


class OpenOutputDirOperator(Operator):
    """ Open file browser at output dir. """
    bl_idname = "scene.zpy_open_output_dir"
    bl_label = "Open Output Dir"
    bl_description = "Open file browser at output dir."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        zpy.file.open_folder_in_explorer(context.scene.zpy_output_path)
        return {'FINISHED'}


class RenderPanel(bpy.types.Panel):
    """ UI for the addon that is visible in Blender. """
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Render"
    bl_category = "ZumoLabs"

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
