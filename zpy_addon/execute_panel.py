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


class RunOperator(Operator):
    """ Launch the run script in Blender's texts. """
    bl_idname = "scene.zpy_run"
    bl_label = "Run Sim"
    bl_description = "Launch the run script in Blender's texts."
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            # Save the state of the sim before the run script was executed
            bpy.ops.wm.save_mainfile()
        except RuntimeError as e:
            log.warning(f'When saving sim before run: {e}')
        try:
            zpy.blender.use_gpu()
            zpy.blender.parse_config('config')
            zpy.blender.run_text('run')
        except Exception as e:
            log.error(f'Executing script failed with exception {e}')
        try:
            # Return to the state of the sim before the run script was executed
            bpy.ops.wm.revert_mainfile()
        except RuntimeError as e:
            log.warning(f'When saving sim before run: {e}')
        return {'FINISHED'}


class RenderOperator(Operator):
    """ Render out single image (rgb, segmented, depth). """
    bl_idname = "scene.zpy_render"
    bl_label = "Render Frame"
    bl_description = "Render out segmented images."
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        # TODO: Make sure sim is good to render?
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


class SCENE_PT_ExecutePanel(bpy.types.Panel):
    """ UI for the addon that is visible in Blender. """
    bl_idname="SCENE_PT_ExecutePanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Execute"
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
        row.operator(
            'scene.zpy_run',
            text='Run',
            icon='TRIA_RIGHT',
        )