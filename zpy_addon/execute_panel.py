"""
    Rendering panel and functions.
"""
import importlib
import logging
from pathlib import Path

import bpy
import zpy
import gin
from bpy.types import Operator

log = logging.getLogger(__name__)

if "bpy" in locals():
    importlib.reload(zpy)


class RunOperator(Operator):
    """Launch the run script in Blender's texts."""

    bl_idname = "scene.zpy_run"
    bl_label = "Run Sim"
    bl_description = "Launch the run script in Blender's texts."
    bl_category = "ZPY"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # Set the logger levels
        zpy.logging.set_log_levels("info")
        # Get the run text
        run_text = bpy.data.texts.get("run", None)
        if run_text is None:
            raise ValueError(
                'Running a sim requires a run text, could not find in text with name "run".'
            )
        # HACK: Gin will complain when this module is re-initialized
        gin.enter_interactive_mode()
        with gin.unlock_config():
            run_text_as_module = run_text.as_module()
        # Parse the gin-config text block
        zpy.blender.parse_config("config")
        # Execute the run function inside the run text
        run_text_as_module.run()
        return {"FINISHED"}


class RenderOperator(Operator):
    """Render out single image (rgb, segmented, depth)."""

    bl_idname = "scene.zpy_render"
    bl_label = "Render Frame"
    bl_description = "Render out segmented images."
    bl_category = "ZPY"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        # TODO: Make sure sim is good to render?
        return True

    def execute(self, context):
        context.space_data.shading.color_type = "OBJECT"

        # Image names
        rgb_image_name = zpy.files.make_rgb_image_name(0)
        cseg_image_name = zpy.files.make_cseg_image_name(0)
        iseg_image_name = zpy.files.make_iseg_image_name(0)
        depth_image_name = zpy.files.make_depth_image_name(0)

        # Output path
        output_path = Path(context.scene.zpy_output_path)

        # Save renders to file
        zpy.render.render(
            rgb_path=output_path / rgb_image_name,
            iseg_path=output_path / iseg_image_name,
            cseg_path=output_path / cseg_image_name,
            depth_path=output_path / depth_image_name,
        )

        return {"FINISHED"}


class SCENE_PT_ExecutePanel(bpy.types.Panel):
    """UI for the addon that is visible in Blender."""

    bl_idname = "SCENE_PT_ExecutePanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Execute"
    bl_category = "ZPY"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(
            "scene.zpy_render",
            text="Render",
            icon="FILE_IMAGE",
        )
        row = layout.row()
        row.operator(
            "scene.zpy_run",
            text="Run (Debug)",
            icon="TRIA_RIGHT",
        )
