"""
    Export panel and functions.
    
    TODO: Add addon preferences for setting custom permanent default path
    TODO: Disable nodes option
    TODO: Handle relative path of the blend internally
    
"""

import importlib
import logging
import os
import sys
from datetime import date
import time
from pathlib import Path

import bpy

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
    bpy.types.Scene.zpy_scene_name = bpy.props.StringProperty(
        name="Scene Name",
        description="Name of the scene, must match data portal.",
        default="default",
        # Function to be called when this value is modified, This
        # function must take 2 values (self, context) and return None.
        update=_update_scene_name,
    )
    bpy.types.Scene.zpy_scene_version = bpy.props.StringProperty(
        name="Scene Version",
        description="Version of the scene, must match data portal.",
        default="0",
        # Function to be called when this value is modified, This
        # function must take 2 values (self, context) and return None.
        update=_update_scene_version,
    )
    bpy.types.Scene.zpy_export_path = bpy.props.StringProperty(
        name='Export Path',
        description="Export path for packaged zumo scenes.",
        default='',
        subtype='DIR_PATH',
        # Function to be called when this value is modified, This
        # function must take 2 values (self, context) and return None.
        update=_update_export_path,
    )


def _update_scene_name(self, context) -> None:
    """ Verify and update the scene name. """
    _scene_name = context.scene.zpy_scene_name
    # All lowercase
    _scene_name = _scene_name.lower()
    # Maximum 10 letters
    _scene_name = _scene_name[:10]
    context.scene.zpy_scene_name = _scene_name


def _update_scene_version(self, context) -> None:
    """ Verify and update the scene version. """
    try:
        int(context.scene.zpy_scene_version)
    except ValueError:
        log.warning('Scene version must be a int')
    context.scene.zpy_scene_version = str(
        abs(int(context.scene.zpy_scene_version)))


def _update_export_path(self, context) -> None:
    """ TODO: Is this design pattern required? """
    verify_export_path(context)


def verify_export_path(context) -> None:
    """ Verify and update the export path. """
    if not Path(context.scene.zpy_export_path).exists():
        log.warning('Export path does not exist, using blendfile path.')
        context.scene.zpy_export_path = str(
            Path(context.blend_data.filepath).parent)


class OpenExportDirOperator(bpy.types.Operator):
    """ Open file browser at export dir. """
    bl_idname = "scene.zpy_open_export_dir"
    bl_label = "Open Export Dir"
    bl_description = "Open file browser at export dir."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        verify_export_path(context)        
        zpy.file.open_folder_in_explorer(context.scene.zpy_export_path)
        return {'FINISHED'}


class CleanUpDirOperator(bpy.types.Operator):
    """ Clean up and package scene into export dir. """
    bl_idname = "scene.zpy_cleanup_scene"
    bl_label = "Clean Up Export Dir"
    bl_description = "Clean up export dir."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Make sure export path is valid
        verify_export_path(context)
        # Remove any backup blender files
        zpy.file.remove_files_with_suffix(
            path=context.scene.zpy_export_path,
            exts=['.blend1', '.blend2', '.blend3'],
        )
        # Remove any existing nfo files
        zpy.file.remove_files_with_suffix(
            path=context.scene.zpy_export_path,
            exts=['.nfo'],
        )
        # TODO: Scene based clean up collections and objects listings (in the text editor)
        # TODO: Remove the custom scene scripts that are not needed for staging (keep run, config, categories for now)
        return {'FINISHED'}


class ExportOperator(bpy.types.Operator):
    """ Export scene for ingest to Data Portal. """
    bl_idname = "scene.zpy_export_scene"
    bl_label = "Export scene"
    bl_description = "Export scene for ingest to Data Portal."
    bl_category = "ZumoLabs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Clean scene before every export
        bpy.ops.scene.zpy_cleanup_scene()

        # Make sure export path is valid
        verify_export_path(context)
        
        # Create export directory in the Blender filepath
        export_dir_name = f'{context.scene.zpy_scene_name}_v{context.scene.zpy_scene_version}'
        export_path = Path(context.scene.zpy_export_path) / export_dir_name
        zpy.file.verify_path(export_path, make=True)

        # Keep track of original Blender filepath
        original_filepath = context.blend_data.filepath

        # Fix all the asset paths by packing them into the .blend
        # file and then un-packing them into a 'textures' folder.
        try:
            bpy.ops.file.make_paths_absolute()
            bpy.ops.file.make_paths_relative()
            bpy.ops.file.pack_all()
            bpy.ops.wm.save_as_mainfile(
                filepath=str(export_path / 'main.blend'),
                copy=True
            )
            bpy.ops.file.unpack_all(method='WRITE_LOCAL')
        except Exception as e:
            self.report({'ERROR'}, e)
            log.warning(f'Exception when exporting: {e}')
            return {'CANCELLED'}

        # Save nfo file with some meta information
        save_time = time.strftime("%m%d%Y_%H%M_%S")
        nfo_file = export_path / \
            f'v{context.scene.zpy_scene_version}_{save_time}.nfo'
        nfo_text = f'version: {context.scene.zpy_scene_version} \n'
        nfo_text += f'version: {context.scene.zpy_scene_version} \n'
        nfo_text += f'save_time: {save_time} \n'
        nfo_text += f'zpy_version: {zpy.__version__} \n'
        nfo_text += f'zpy_path: {zpy.__file__} \n'
        nfo_text += f'zpy_addon_path: {__file__} \n'
        nfo_file.write_text(nfo_text)

        # TODO: Export glTF into zip directory

        # Zip up the exported directory for easy upload
        zpy.file.zip_file(
            in_path=export_path,
            zip_path=Path(context.scene.zpy_export_path) / f'{export_dir_name}.zip',
        )

        # Re-save scene to original filepath
        bpy.ops.wm.save_as_mainfile(
            filepath=original_filepath,
            copy=False
        )

        # Clean scene after every export
        bpy.ops.scene.zpy_cleanup_scene()

        return {'FINISHED'}


class ExportPanel(bpy.types.Panel):
    """ UI for the addon that is visible in Blender. """
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Export"
    bl_category = "ZumoLabs"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        row.operator(
            'scene.zpy_export_scene',
            text='Export Scene',
            icon='EXPORT',
        )
        row = layout.row()
        row.prop(scene, "zpy_scene_name", text="Name")
        row = layout.row()
        row.prop(scene, "zpy_scene_version", text="Version")
        row = layout.row()
        row.label(text="Export Path")
        row = layout.row()
        row.prop(scene, "zpy_export_path", text="")
        row = layout.row()
        row.operator(
            'scene.zpy_open_export_dir',
            text='Open',
            icon='FILEBROWSER',
        )
        row.operator(
            'scene.zpy_cleanup_scene',
            text='Clean',
            icon='PACKAGE',
        )
