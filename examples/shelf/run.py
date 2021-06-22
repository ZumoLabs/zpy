"""
    Shelf with cereal boxes (and other boxes) on it.
"""

import logging
import random
from typing import Tuple

import bpy
import gin
import zpy

log = logging.getLogger('zpy')


@gin.configurable('run')
@zpy.blender.save_and_revert
def run(
    number_of_shelves: Tuple[int] = (2, 6),
    horizontal_length_of_shelves: Tuple[int] = (2, 5),
    density_of_objects_modifier: Tuple[int] = (7, 60),
    number_of_random_materials: int = 50,
    jitter_materials: bool = True,
    jitter_objects: bool = True,
):

    # Random seed results in unique behavior
    zpy.blender.set_seed()

    # Create the saver object
    saver = zpy.saver_image.ImageSaver(
        description='Shelf of cereal boxes',
    )

    # Create seg colors
    zpy.color.reset()
    box_cereal_seg_color = zpy.color.random_color(output_style='frgb')
    box_distractor_seg_color = zpy.color.random_color(output_style='frgb')

    # HACK: Save the random color idx after creating category colors
    post_category_color_idx = zpy.color.RANDOM_COLOR_IDX + 1

    # Add the categories
    saver.add_category(name='box.cereal',
                       supercategories=['item', 'box'],
                       color=box_cereal_seg_color)
    saver.add_category(name='box.distractor',
                       supercategories=['item', 'box'],
                       color=box_distractor_seg_color)

    # Pre-create a bunch of random textures
    random_materials = [zpy.material.random_texture_mat()
                        for _ in range(number_of_random_materials)]

    # Save the positions of objects so we can jitter them later
    zpy.objects.save_pose('Camera')
    zpy.objects.save_pose('Light')
    zpy.objects.save_pose('Light.001')
    zpy.objects.save_pose('Light.002')

    # Run the scene.
    for frame in zpy.blender.step():

        # Return camera and objs to original positions
        zpy.objects.restore_pose('Camera')
        zpy.objects.restore_pose('Light')
        zpy.objects.restore_pose('Light.001')
        zpy.objects.restore_pose('Light.002')

        # Pick a random HDRI
        zpy.hdris.random_hdri()

        # Jitter the camera pose
        zpy.objects.jitter('Camera',
                           translate_range=(
                               (-1, 5),
                               (-0.5, 0.5),
                               (-0.1, 0.6),
                           ))

        # Make the camera point "look at" an empty object in the sim
        zpy.camera.look_at('Camera', bpy.data.objects["LookAtObject"].location)

        # Get lights and randomize their energy output
        for obj in bpy.data.lights:
            bpy.data.objects[obj.name].hide_render = bool(random.randint(0, 1))
            bpy.data.objects[obj.name].data.energy = random.randint(100, 1500)

        # Random seed determine which locations will spawn objects
        bpy.data.node_groups["SpawnerNodes"].nodes["Objects to Distribute"].inputs[3].default_value = frame

        # Determines density of objects on shelves
        bpy.data.node_groups["SpawnerNodes"].nodes["Distance and Density"].inputs[2].default_value = random.randint(
            density_of_objects_modifier[0], density_of_objects_modifier[1])

        # Length (horizontal) of shelves in sim
        shelf_X = random.randint(horizontal_length_of_shelves[0], horizontal_length_of_shelves[1])
        bpy.data.objects["SHELVES"].scale[0] = shelf_X
        bpy.data.objects["Spawner"].modifiers["ShelfHeight"].count = shelf_X

        # Number of shelves (vertical) in sim
        shelf_Z = random.randint(number_of_shelves[0], number_of_shelves[1])
        bpy.data.objects["Spawner"].modifiers["ShelfHeight"].count = shelf_Z
        bpy.data.objects["SHELVES"].modifiers["ShelfNumber"].count = shelf_Z

        # Make instances in spawner object (called "Spawner") actual real objects,
        # which allows us to segement and catagorize them as individual objects
        zpy.objects.select('Spawner')
        bpy.ops.object.duplicates_make_real()
        bpy.ops.object.make_single_user(
            object=True, obdata=True, material=False, animation=False)

        # HACK: Re-set random color index so we don't run out of colors
        zpy.color.reset(post_category_color_idx)

        # Loop through all the objects in Spawner Collection
        for obj in bpy.data.collections['SPAWNER'].all_objects:
            # Ignore spawner object.
            if obj.name == 'Spawner':
                continue
            # For all other objects, put them into Spawned Collection
            bpy.data.collections['SPAWNED'].objects.link(obj)
            bpy.data.collections['SPAWNER'].objects.unlink(obj)

        # Loop through objects now in Spawned Collection
        for obj in bpy.data.collections['SPAWNED'].all_objects:
            # Jitter the material
            for i in range(len(obj.material_slots)):
                if jitter_materials:
                    zpy.material.jitter(obj.material_slots[i].material)
            if jitter_objects:
                zpy.objects.jitter_mesh(obj)
            zpy.objects.segment(obj, name=obj.name)
            # Segment objects depending on category
            if 'box.cereal' in obj.name:
                zpy.objects.segment(obj, name='box.cereal',
                                    color=box_cereal_seg_color, as_category=True)
            if 'box.distractor' in obj.name:
                # Make a list of the Box Objects and segment them
                zpy.objects.segment(obj, name='box.distractor',
                                    color=box_distractor_seg_color,
                                    as_category=True)
                # For distractor boxes, randomize scale a little
                zpy.objects.jitter(obj,
                                   scale_range=(
                                       (0.8, 1.5),
                                       (0.7, 1.1),
                                       (0.7, 1.25),
                                   ))

        # Randomize texture of shelf, floors and walls
        for obj in bpy.data.collections['BACKGROUND'].all_objects:
            for i in range(len(obj.material_slots)):
                # Pick one of the random materials
                obj.material_slots[i].material = random.choice(
                    random_materials)
                if jitter_materials:
                    zpy.material.jitter(obj.material_slots[i].material)
                 # Sets the material relative to the object
                obj.material_slots[i].link = 'OBJECT'

        # Name for each of the output images
        cseg_image_name = zpy.files.make_cseg_image_name(frame)
        rgb_image_name = zpy.files.make_rgb_image_name(frame)
        iseg_image_name = zpy.files.make_iseg_image_name(frame)
        depth_image_name = zpy.files.make_depth_image_name(frame)

        # Render image
        zpy.render.render(
            rgb_path=saver.output_dir / rgb_image_name,
            cseg_path=saver.output_dir / cseg_image_name,
            iseg_path=saver.output_dir / iseg_image_name,
            depth_path=saver.output_dir / depth_image_name,
        )

        # Add images to saver
        saver.add_image(
            name=rgb_image_name,
            style='default',
            output_path=saver.output_dir / rgb_image_name,
            frame=frame,
        )
        saver.add_image(
            name=iseg_image_name,
            style='segmentation',
            output_path=saver.output_dir / iseg_image_name,
            frame=frame,
        )
        saver.add_image(
            name=depth_image_name,
            style='depth',
            output_path=saver.output_dir / depth_image_name,
            frame=frame,
        )
        saver.add_image(
            name=cseg_image_name,
            style='segmentation',
            output_path=saver.output_dir / cseg_image_name,
            frame=frame,
        )

        # Add annotation to segmentation image
        for obj in bpy.data.collections['SPAWNED'].all_objects:
            if 'box.' in obj.name:
                saver.add_annotation(
                    image=rgb_image_name,
                    seg_image=iseg_image_name,
                    seg_color=tuple(obj.seg.instance_color),
                    category=obj.seg.category_name,
                )

        # Delete the spawned objects to start a new frame of the simulation
        zpy.objects.empty_collection(
            bpy.data.collections['SPAWNED'], method='context')

    # Write out annotations
    saver.output_annotated_images()
    saver.output_meta_analysis()

    # ZUMO Annotations
    zpy.output_zumo.OutputZUMO(saver).output_annotations()

    # COCO Annotations
    zpy.output_coco.OutputCOCO(saver).output_annotations()


if __name__ == "__main__":

    # Set the logger levels
    zpy.logging.set_log_levels('info')

    # Parse the gin-config text block
    zpy.blender.parse_config('config')

    # Run the scene
    run()
