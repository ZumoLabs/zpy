"""
    Export panel and functions.
"""
import importlib
import logging
import time
from pathlib import Path

import bpy
import zpy

log = logging.getLogger(__name__)

if "bpy" in locals():
    importlib.reload(zpy)


def registerSceneProperties():
    """ Properties applied to scenes."""
    bpy.types.Scene.zpy_sim_name = bpy.props.StringProperty(
        name="Sim Name",
        description="Name of the scene, must match data portal.",
        default="default",
    )
    bpy.types.Scene.zpy_sim_version = bpy.props.StringProperty(
        name="Sim Version",
        description="Version of the scene, must match data portal.",
        default="0",
    )
    bpy.types.Scene.zpy_export_dir = bpy.props.StringProperty(
        name='Export Directory Path',
        description="Path to directory for exporting packaged zumo scenes.",
        default=str(zpy.files.default_temp_path()),
        subtype='DIR_PATH',
    )
    bpy.types.Scene.zpy_export_path = bpy.props.StringProperty(
        name='Export Path',
        description="Export path for this zumo scene.",
        default=str(zpy.files.default_temp_path()),
        subtype='DIR_PATH',
    )

class OpenExportDirOperator(bpy.types.Operator):
    """ Open file browser at export dir. """
    bl_idname = "scene.zpy_open_export_dir"
    bl_label = "Open Export Dir"
    bl_description = "Open file browser at export dir."
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    def execute(self, context):
        zpy.files.open_folder_in_explorer(
            context.scene.zpy_export_dir, make=True)
        return {'FINISHED'}


class CleanUpDirOperator(bpy.types.Operator):
    """ Clean up and package sim into export dir. """
    bl_idname = "scene.zpy_cleanup_sim"
    bl_label = "Clean Up Export Dir"
    bl_description = "Clean up export dir."
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    def execute(self, context):
        log.info('Cleaning up scene.')
        # Remove any backup blender files
        zpy.files.remove_files_with_suffix(
            path=context.scene.zpy_export_path,
            exts=['.blend1', '.blend2', '.blend3'],
        )
        # TODO: Scene based clean up collections and objects listings (in the text editor)
        # TODO: Remove the custom scene scripts that are not needed for staging (keep run, config, categories for now)
        return {'FINISHED'}


class ExportOperator(bpy.types.Operator):
    """ Export sim for ingest to Data Portal. """
    bl_idname = "scene.zpy_export_sim"
    bl_label = "Export sim"
    bl_description = "Export sim for ingest to Data Portal."
    bl_category = "ZPY"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Shows progress cursor in Blender UI.
        log.info('Export Started.')
        bpy.context.window_manager.progress_begin(0, 100)

        # Clean scene before every export
        bpy.ops.scene.zpy_cleanup_sim()

        # Create export directory in the Blender filepath
        export_dir_name = f'{context.scene.zpy_sim_name}_v{context.scene.zpy_sim_version}'
        export_path = Path(context.scene.zpy_export_dir) / export_dir_name
        zpy.files.verify_path(export_path, make=True)

        # Set the scene export path
        context.scene.zpy_export_path = str(export_path)

        # Find missing files before export
        log.info('Export Step 1 of 4: Checking for any missing files.')
        bpy.context.window_manager.progress_update(10)
        _path = zpy.files.verify_path('$ASSETS', make=False)
        bpy.ops.file.find_missing_files(directory=str(_path))

        # Fix all the asset paths by packing them into the .blend
        # file and then un-packing them into a 'textures' folder.
        try:
            bpy.ops.wm.save_as_mainfile(
                filepath=str(export_path / 'main.blend'),
                compress=False,
                relative_remap=True,
            )
            log.info('Export Step 2 of 4: Packing files into .blend.')
            bpy.context.window_manager.progress_update(30)
            bpy.ops.file.make_paths_absolute()
            bpy.ops.file.make_paths_relative()
            bpy.ops.file.pack_all()
            bpy.ops.file.unpack_all(method='WRITE_LOCAL')
            bpy.ops.wm.save_as_mainfile(
                filepath=str(export_path / 'main.blend'),
                compress=False,
                relative_remap=True,
            )
        except Exception as e:
            self.report({'ERROR'}, str(e))
            log.warning(f'Exception when exporting: {e}')
            return {'CANCELLED'}

        log.info('Export Step 3 of 4: Saving meta-information.')
        bpy.context.window_manager.progress_update(70)

        # Output scene information in ZUMO_META
        zpy.files.write_json(
            export_path / 'ZUMO_META.json',
            zpy.blender.scene_information(),
        )

        # TODO: Export glTF into zip directory

        # Clean up scene before zipping up
        bpy.ops.scene.zpy_cleanup_sim()

        # Zip up the exported directory for easy upload
        log.info('Export Step 4 of 4: Zipping up package.')
        bpy.context.window_manager.progress_update(90)
        zpy.files.zip_file(
            in_path=export_path,
            zip_path=Path(context.scene.zpy_export_dir) /
            f'{export_dir_name}.zip',
        )

        log.info('Export Completed.')
        bpy.context.window_manager.progress_end()
        return {'FINISHED'}


class SCENE_PT_ExportPanel(bpy.types.Panel):
    """ UI for the addon that is visible in Blender. """
    bl_idname = "SCENE_PT_ExportPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Export"
    bl_category = "ZPY"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        row.operator(
            'scene.zpy_export_sim',
            text='Export Sim',
            icon='EXPORT',
        )
        row = layout.row()
        row.prop(scene, "zpy_sim_name", text="Name")
        row = layout.row()
        row.prop(scene, "zpy_sim_version", text="Version")
        row = layout.row()
        row.label(text="Export Path")
        row = layout.row()
        row.prop(scene, "zpy_export_dir", text="")
        row = layout.row()
        row.operator(
            'scene.zpy_open_export_dir',
            text='Open',
            icon='FILEBROWSER',
        )
        row.operator(
            'scene.zpy_cleanup_sim',
            text='Clean',
            icon='PACKAGE',
        )
