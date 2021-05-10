"""
    Segment panel and functions.
"""
import importlib
import logging
from typing import Tuple

import bpy
import zpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

log = logging.getLogger(__name__)

if "bpy" in locals():
    importlib.reload(zpy)


def registerObjectProperties():
    """Properties applied to object."""
    bpy.types.Object.seg = bpy.props.PointerProperty(type=SegmentableProperties)


def registerSceneProperties():
    """Properties applied to scenes."""
    bpy.types.Scene.categories = bpy.props.CollectionProperty(type=CategoryProperties)
    bpy.types.Scene.categories_enum = bpy.props.EnumProperty(
        name="Category",
        description="Category for this object.",
        default=None,
        items=_category_items,
        update=_category_update,
    )


class CategoryProperties(bpy.types.PropertyGroup):
    """Segmentation category is a property of one or many objects."""

    name: bpy.props.StringProperty(
        name="Category Name",
        description="String name of the category.",
    )
    color: bpy.props.FloatVectorProperty(
        name="Category Color",
        subtype="COLOR",
        description="Category color for segmentation.",
    )


def _category_items(self, context):
    """Get current categories."""
    _categories_enum = []
    for i, (name, category) in enumerate(bpy.context.scene.categories.items()):
        # Add category to ENUM tuple
        _categories_enum.append(
            (
                # First item is used for Python access.
                str(i),
                name,
                zpy.color.frgb_to_hex(category.color),
            )
        )
    return _categories_enum


def _category_update(self, context):
    """Update the category."""
    if context.selected_objects:
        # Use the value of the category enum dropdown
        category = context.scene.categories[int(context.scene.categories_enum)]
        for obj in zpy.objects.for_obj_in_selected_objs(context):
            zpy.objects.segment(
                obj=obj,
                name=category.name,
                color=category.color,
                as_category=True,
            )


class SegmentableProperties(bpy.types.PropertyGroup):
    category_name: bpy.props.StringProperty(
        name="Category Name",
        description="String name of the category.",
        default="",
    )
    category_color: bpy.props.FloatVectorProperty(
        name="Category Color",
        subtype="COLOR",
        description="Category color for segmentation.",
    )
    instance_name: bpy.props.StringProperty(
        name="Instance Name",
        description="String name of the instance.",
        default="",
    )
    instance_color: bpy.props.FloatVectorProperty(
        name="Instance Color",
        subtype="COLOR",
        description="Instance color for segmentation.",
    )


class SegmentInstanceMany(Operator):
    """Segment the selected objects/parts.

    Each object will be segmented as a unique object.

    """

    bl_idname = "object.zpy_segment_instance_many"
    bl_label = "Segment Instance (Many)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        context.space_data.shading.color_type = "OBJECT"
        for obj in zpy.objects.for_obj_in_selected_objs(context):
            zpy.objects.segment(obj=obj, name=obj.name)
        return {"FINISHED"}


class SegmentInstanceSingle(Operator):
    """Segment the selected objects/parts.

    All objects will be segmented as a single instance.

    """

    bl_idname = "object.zpy_segment_instance_single"
    bl_label = "Segment Instance (Single)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        context.space_data.shading.color_type = "OBJECT"
        # Pick a random color and instance name
        _name = context.selected_objects[0].name
        _color = zpy.color.random_color(output_style="frgb")
        for obj in zpy.objects.for_obj_in_selected_objs(context):
            zpy.objects.segment(obj=obj, name=_name, color=_color)
        return {"FINISHED"}


class VisualizeInstance(Operator):
    """Visualize the instance colors on objects in scene."""

    bl_idname = "object.zpy_visualize_instance"
    bl_label = "Visualize Instances"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.space_data.shading.color_type = "OBJECT"
        # Loop through all objects in the scene
        for obj in context.scene.objects:
            if not obj.type == "MESH":
                continue
            context.view_layer.objects.active = obj
            if obj.seg.instance_color is not None:
                obj.color = zpy.color.frgb_to_frgba(obj.seg.instance_color)
            else:
                obj.color = zpy.color.default_color(output_style="frgba")
        return {"FINISHED"}


class VisualizeCategory(Operator):
    """Visualize the category colors on objects in scene."""

    bl_idname = "object.zpy_visualize_category"
    bl_label = "Visualize Categories"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.space_data.shading.color_type = "OBJECT"
        # Loop through all objects in the scene
        for obj in context.scene.objects:
            if not obj.type == "MESH":
                continue
            context.view_layer.objects.active = obj
            if obj.seg.category_color is not None:
                obj.color = zpy.color.frgb_to_frgba(obj.seg.category_color)
            else:
                obj.color = zpy.color.default_color()
        return {"FINISHED"}


class ResetSegData(Operator):
    """Reset the segmentation data on the selected objects/parts."""

    bl_idname = "object.zpy_reset_seg_data"
    bl_label = "Reset Segmentation Data"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        context.space_data.shading.color_type = "OBJECT"
        for obj in context.selected_objects:
            # Only meshes or empty objects TODO: Why the empty objects
            if not (obj.type == "MESH" or obj.type == "EMPTY"):
                continue
            obj.seg.instance_name = ""
            obj.seg.instance_color = zpy.color.default_color(output_style="frgb")
            obj.seg.category_name = "default"
            obj.seg.category_color = zpy.color.default_color(output_style="frgb")
            obj.color = zpy.color.default_color(output_style="frgba")
        return {"FINISHED"}


def _reset_categories(context):
    """Reset the scene categories."""
    # Clean out the scene-level category dict
    for _ in range(len(context.scene.categories)):
        context.scene.categories.remove(0)
    # Reset all categories
    for obj in zpy.objects.for_obj_in_selected_objs(context):
        obj.seg.category_name = "default"
        obj.seg.category_color = zpy.color.default_color(output_style="frgb")
        obj.color = zpy.color.default_color(output_style="frgba")


def _add_category(context, name: str = None, color: Tuple[float] = None) -> None:
    """Add category to enum category property."""
    if name in context.scene.categories.keys():
        log.warning(f"Skipping duplicate category {name}.")
        return
    if color is None:
        color = zpy.color.random_color(output_style="frgb")
        log.info(f"Choosing random color for category {name}: {color}")
    # Add category to categories dict
    new_category = context.scene.categories.add()
    new_category.name = name
    new_category.color = color


class CategoriesFromText(Operator):
    """Populate categories from text block."""

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

        assert (
            category_text is not None
        ), "Category text block must exist for segmentation."

        # Activate the categories text block in the text editor
        for area in context.screen.areas:
            if area.type == "TEXT_EDITOR":
                space = area.spaces.active
                space.text = category_text

        _reset_categories(context)

        for line in category_text.lines:
            _add_category(context, name=line.body)
        return {"FINISHED"}


class CategoriesFromZUMOJSON(Operator, ImportHelper):
    """Populate categories from Zumo JSON."""

    bl_idname = "object.zpy_categories_from_zumo"
    bl_description = "Categories from Zumo JSON"
    bl_label = "Import"

    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        zumo_json = zpy.files.read_json(self.filepath)
        categories = zumo_json.get("categories", None)
        assert categories is not None, "ZUMO JSON does not have categories."
        _reset_categories(context)
        for category in categories.values():
            _add_category(
                context,
                name=category.get("name", None),
                color=category.get("color", None),
            )
        return {"FINISHED"}


class SCENE_PT_SegmentPanel(bpy.types.Panel):
    """UI for the addon that is visible in Blender."""

    bl_idname = "SCENE_PT_SegmentPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Segment"
    bl_category = "ZPY"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Segment Selected Objects")
        row = layout.row()
        row.operator(
            "object.zpy_segment_instance_single",
            text="Single",
            icon="USER",
        )
        row.operator(
            "object.zpy_segment_instance_many",
            text="Many",
            icon="COMMUNITY",
        )
        row = layout.row()
        row.prop(context.scene, "categories_enum", text="")
        row = layout.row()
        row.label(text="Visualize")
        row = layout.row()
        row.operator(
            "object.zpy_visualize_instance",
            text="Visualize Instances",
            icon="HIDE_OFF",
        )
        row = layout.row()
        row.operator(
            "object.zpy_visualize_category",
            text="Visualize Categories",
            icon="HIDE_OFF",
        )

        row = layout.row()
        row.label(text="Load Categories")
        row = layout.row()
        row.operator(
            "object.zpy_categories_from_text",
            text="Text",
            icon="TEXT",
        )
        row.operator(
            "object.zpy_categories_from_zumo",
            text="Json",
            icon="FILEBROWSER",
        )

        row = layout.row()
        row.label(text="Selected Object Data")
        row = layout.row()
        row.operator(
            "object.zpy_reset_seg_data",
            text="Reset Seg Data",
            icon="FILE_REFRESH",
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
