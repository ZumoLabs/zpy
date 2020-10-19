"""
    Segment panel and functions.
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
from bpy_extras.io_utils import ExportHelper, ImportHelper

log = logging.getLogger('zpy')

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


def registerObjectProperties():
    """ Properties applied to object."""
    bpy.types.Object.seg = bpy.props.PointerProperty(
        type=SegmentableProperties)


def registerSceneProperties():
    """ Properties applied to scenes."""
    bpy.types.Scene.categories = bpy.props.CollectionProperty(
        type=CategoryProperties
    )
    bpy.types.Scene.categories_enum = bpy.props.EnumProperty(
        name="Category",
        description="Category for this object.",
        default=None,
        items=_category_items,
        update=_category_update,
    )


class CategoryProperties(bpy.types.PropertyGroup):
    """ Segmentation category is a property of one or many objects. """
    name: bpy.props.StringProperty(
        name="Category Name",
        description="String name of the category.",
    )
    color: bpy.props.FloatVectorProperty(
        name="Category Color",
        subtype='COLOR',
        description="Category color for segmentation.",
    )


def _category_items(self, context):
    """ Get current categories. """
    _categories_enum = []
    for i, (name, category) in enumerate(bpy.context.scene.categories.items()):
        # Add category to ENUM tuple
        _categories_enum.append((
            # First item is used for Python access.
            str(i),
            name,
            zpy.color.frgb_to_hex(category.color),
        ))
    return _categories_enum


def _category_update(self, context):
    """ Update the category. """
    if context.selected_objects:
        # Make sure there is an AOV pass for category colors
        zpy.render.make_aov_pass('category')
        # Use the value of the category enum dropdown
        category = context.scene.categories[int(context.scene.categories_enum)]
        for obj in _for_obj_in_selected_objs(context):
            obj.seg.category_name = category.name
            obj.seg.category_color = category.color
            obj.color = zpy.color.frgb_to_frgba(category.color)
            # Populate vertex colors
            populate_vertex_colors(context,
                                   obj,
                                   zpy.color.frgb_to_srgba(category.color),
                                   'category')
            # Add category aov output node to object material
            zpy.material.make_aov_material_output_node(
                obj=obj, style='category')


def _for_obj_in_selected_objs(context):
    """ Safe iterable for selected objects. """
    for obj in context.selected_objects:
        # Only meshes or empty objects TODO: Why the empty objects
        if not (obj.type == 'MESH' or obj.type == 'EMPTY'):
            continue
        # Make sure object exists in the scene
        if bpy.data.objects.get(obj.name, None) is None:
            continue
        yield obj


def populate_vertex_colors(context,
                           obj: bpy.types.Object,
                           color_rgba: tuple,
                           seg_type: str = 'instance'):
    """Fill the given Vertex Color Layer with the color parameter values"""
    if not obj.type == 'MESH':
        return
    # Remove any existing vertex color data
    if len(obj.data.vertex_colors):
        for vcol in obj.data.vertex_colors.keys():
            if seg_type in vcol:
                obj.data.vertex_colors.remove(obj.data.vertex_colors[seg_type])
    # Add new vertex color data
    obj.data.vertex_colors.new(name=seg_type)
    # HACK: Make sure selected object is the active object
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    context.view_layer.objects.active = obj
    # Iterate through each vertex in the mesh
    i = 0
    for poly in obj.data.polygons:
        for _ in poly.loop_indices:
            obj.data.vertex_colors[seg_type].data[i].color = color_rgba
            i += 1


class SegmentableProperties(bpy.types.PropertyGroup):
    category_name: bpy.props.StringProperty(
        name="Category Name",
        description="String name of the category.",
        default='',
    )
    category_color: bpy.props.FloatVectorProperty(
        name="Category Color",
        subtype='COLOR',
        description="Category color for segmentation.",
    )
    instance_name: bpy.props.StringProperty(
        name="Instance Name",
        description="String name of the instance.",
        default='',
    )
    instance_color: bpy.props.FloatVectorProperty(
        name="Instance Color",
        subtype='COLOR',
        description="Instance color for segmentation.",
    )


class SegmentInstanceMany(Operator):
    """ Segment the selected objects/parts.

    Each object will be segmented as a unique object.

    """
    bl_idname = "object.zpy_segment_instance_many"
    bl_label = "Segment Instance (Many)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        context.space_data.shading.color_type = 'OBJECT'
        for obj in _for_obj_in_selected_objs(context):
            bpy.context.view_layer.objects.active = obj
            # Pick a random color for every sub-object
            _color = zpy.color.random_color(output_style='frgb')
            # Set properties for object
            obj.seg.instance_name = obj.name
            obj.seg.instance_color = _color
            obj.color = zpy.color.frgb_to_frgba(_color)
            # Populate vertex colors
            populate_vertex_colors(context,
                                   obj,
                                   zpy.color.frgb_to_srgba(_color),
                                   'instance')
            # Add instance aov output node to object material
            zpy.material.make_aov_material_output_node(
                obj=obj, style='instance')
        # Make sure there is an AOV pass for instance colors
        zpy.render.make_aov_pass('instance')
        return {'FINISHED'}


class SegmentInstanceSingle(Operator):
    """ Segment the selected objects/parts.

    All objects will be segmented as a single instance.

    """
    bl_idname = "object.zpy_segment_instance_single"
    bl_label = "Segment Instance (Single)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        context.space_data.shading.color_type = 'OBJECT'
        # Pick a random color and instance name
        _name = context.selected_objects[0].name
        _color = zpy.color.random_color(output_style='frgb')
        for obj in _for_obj_in_selected_objs(context):
            context.view_layer.objects.active = obj
            # Set properties for object
            obj.seg.instance_name = _name
            obj.seg.instance_color = _color
            obj.color = zpy.color.frgb_to_frgba(_color)
            # Populate vertex colors
            populate_vertex_colors(context,
                                   obj,
                                   zpy.color.frgb_to_srgba(_color),
                                   'instance')
            # Add instance aov output node to object material
            zpy.material.make_aov_material_output_node(
                obj=obj, style='instance')
        # Make sure there is an AOV pass for instance colors
        zpy.render.make_aov_pass('instance')
        return {'FINISHED'}


class VisualizeInstance(Operator):
    """ Visualize the instance colors on objects in scene. """
    bl_idname = "object.zpy_visualize_instance"
    bl_label = "Visualize Instances"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.space_data.shading.color_type = 'OBJECT'
        # Loop through all objects in the scene
        for obj in context.scene.objects:
            if not obj.type == 'MESH':
                continue
            context.view_layer.objects.active = obj
            if obj.seg.instance_color is not None:
                obj.color = zpy.color.frgb_to_frgba(
                    obj.seg.instance_color)
            else:
                obj.color = zpy.color.default_color(output_style='frgba')
        return {'FINISHED'}


class VisualizeCategory(Operator):
    """ Visualize the category colors on objects in scene. """
    bl_idname = "object.zpy_visualize_category"
    bl_label = "Visualize Categories"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.space_data.shading.color_type = 'OBJECT'
        # Loop through all objects in the scene
        for obj in context.scene.objects:
            if not obj.type == 'MESH':
                continue
            context.view_layer.objects.active = obj
            if obj.seg.category_color is not None:
                obj.color = zpy.color.frgb_to_frgba(
                    obj.seg.category_color)
            else:
                obj.color = zpy.color.default_color()
        return {'FINISHED'}


class ResetSegData(Operator):
    """ Reset the segmentation data on the selected objects/parts. """
    bl_idname = "object.zpy_reset_seg_data"
    bl_label = "Reset Segmentation Data"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        context.space_data.shading.color_type = 'OBJECT'
        for obj in context.selected_objects:
            # Only meshes or empty objects TODO: Why the empty objects
            if not (obj.type == 'MESH' or obj.type == 'EMPTY'):
                continue
            obj.seg.instance_name = ''
            obj.seg.instance_color = zpy.color.default_color(
                output_style='frgb')
            obj.seg.category_name = 'default'
            obj.seg.category_color = zpy.color.default_color(
                output_style='frgb')
            obj.color = zpy.color.default_color(output_style='frgba')
        return {'FINISHED'}


def _reset_categories(context):
    """ Reset the scene categories. """
    # Clean out the scene-level category dict
    for _ in range(len(context.scene.categories)):
        context.scene.categories.remove(0)
    # Reset all categories
    for obj in _for_obj_in_selected_objs(context):
        obj.seg.category_name = 'default'
        obj.seg.category_color = zpy.color.default_color(
            output_style='frgb')
        obj.color = zpy.color.default_color(output_style='frgba')


class CategoriesFromText(Operator):
    """ Populate categories from text block. """
    bl_idname = "object.zpy_categories_from_text"
    bl_label = "Categories from Text"

    def execute(self, context):

        # BUG: Clicking "Text" resets all the categories and their colors

        txt = bpy.data.texts
        if "categories" in txt.keys():
            category_text = txt["categories"]

        else:
            txt.new("categories")
            category_text = txt["categories"]

        assert category_text is not None, \
            f'Category text block must exist for segmentation.'

        # Activate the categories text block in the text editor
        for area in context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                space = area.spaces.active
                space.text = category_text

        _reset_categories(context)

        for i, line in enumerate(category_text.lines):
            _category = line.body
            assert isinstance(_category, str), \
                f'Invalid category at row {i}: category is not string.'
            assert _category not in context.scene.categories.keys(), \
                f'Invalid category at row {i}: category is duplicate.'
            # Add category to categories dict
            new_category = context.scene.categories.add()
            new_category.name = _category
            new_category.color = zpy.color.random_color(output_style='frgb')
        return {'FINISHED'}


class CategoriesFromZUMOJSON(Operator, ImportHelper):
    """ Populate categories from Zumo JSON. """
    bl_idname = "object.zpy_categories_from_zumo"
    bl_description = "Categories from Zumo JSON"
    bl_label = "Import"

    filter_glob: bpy.props.StringProperty(
        default='*.json', options={'HIDDEN'})

    def execute(self, context):
        zumo_json = zpy.file.read_json(self.filepath)
        categories = zumo_json.get('categories', None)
        assert categories is not None, \
            f'ZUMO JSON does not have categories.'
        _reset_categories(context)
        for category in categories.values():
            # Add category to categories dict
            new_category = context.scene.categories.add()
            new_category.name = category['name']
            new_category.color = category['color']
        return {'FINISHED'}


class SegmentPanel(bpy.types.Panel):
    """ UI for the addon that is visible in Blender. """
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Segment"
    bl_category = "ZumoLabs"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Segment Selected Objects")
        row = layout.row()
        row.operator(
            'object.zpy_segment_instance_single',
            text='Single',
            icon='USER',
        )
        row.operator(
            'object.zpy_segment_instance_many',
            text='Many',
            icon='COMMUNITY',
        )
        row = layout.row()
        row.prop(context.scene, "categories_enum", text="")
        row = layout.row()
        row.label(text="Visualize")
        row = layout.row()
        row.operator(
            'object.zpy_visualize_instance',
            text='Visualize Instances',
            icon='HIDE_OFF',
        )
        row = layout.row()
        row.operator(
            'object.zpy_visualize_category',
            text='Visualize Categories',
            icon='HIDE_OFF',
        )

        row = layout.row()
        row.label(text="Load Categories")
        row = layout.row()
        row.operator(
            'object.zpy_categories_from_text',
            text='Text',
            icon='TEXT',
        )
        row.operator(
            'object.zpy_categories_from_zumo',
            text='Json',
            icon='FILEBROWSER',
        )

        row = layout.row()
        row.label(text="Selected Object Data")
        row = layout.row()
        row.operator(
            'object.zpy_reset_seg_data',
            text='Reset Seg Data',
            icon='FILE_REFRESH',
        )
        row = layout.row()
        row.label(text="Instance")
        row = layout.row()
        row.prop(context.object.seg, "instance_name", text="")
        row.prop(context.object.seg, "instance_color", text="")
        row = layout.row()
        row.label(text="Category")
        row = layout.row()
        row.prop(context.object.seg, "category_name", text="")
        row.prop(context.object.seg, "category_color", text="")
        row = layout.row()
