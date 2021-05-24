""" Package sim.

Spawns boxes and parcels.

"""
import logging
import math
import os
import random
from pathlib import Path
from typing import List

import bpy
import gin
import mathutils
import zpy

log = logging.getLogger("zpy")


@gin.configurable("run")
@zpy.blender.save_and_revert
def run(
    max_num_boxes: int = 4,
    jitter_mesh: bool = True,
    jitter_box_scale: bool = True,
    jitter_material: bool = True,
):
    """Main run function.

    Any kwargs you put here will show up
    on the Data Portal. Give them types!
    """

    # Random seed results in unique behavior
    zpy.blender.set_seed()

    # Create the saver object
    saver = zpy.saver_image.ImageSaver(
        description="Image of the randomized Amazon boxes",
    )

    # Add the box category to our saver object
    box_seg_color = zpy.color.random_color(output_style="frgb")
    saver.add_category(name="box", color=box_seg_color)

    # Make a list of source box objects
    source_box_objects = []
    for obj in zpy.objects.for_obj_in_collections(
        [
            bpy.data.collections["SOURCES.BOXES"],
        ]
    ):
        zpy.objects.segment(obj, name="box", color=box_seg_color, as_category=True)
        source_box_objects.append(obj.name)

    # Save the position of the camera and light
    zpy.objects.save_pose("Camera")
    zpy.objects.save_pose("Sun")

    # Run the sim.
    for step_idx in zpy.blender.step():

        num_boxes = random.randint(1, max_num_boxes)
        log.info(f"Spawning {num_boxes} boxes.")
        spawned_box_objects = []
        for _ in range(num_boxes):

            # Choose location to spawn boxes
            spawn_point = (
                random.uniform(-0.8, 0.8),
                random.uniform(-0.8, 0.8),
                random.uniform(0.0, 0.1),  # Boxes all spawn above the floor
            )

            # Pick a random object to spawn
            _name = random.choice(source_box_objects)
            log.info(f"Spawning a copy of source box {_name} at {spawn_point}")
            obj = zpy.objects.copy(
                bpy.data.objects[_name],
                collection=bpy.data.collections["SPAWNED"],
                is_copy=True,
            )
            obj.matrix_world = mathutils.Matrix.Translation(spawn_point)
            spawned_box_objects.append(obj)

            # Segment the newly spawned box as an instance
            zpy.objects.segment(obj)

            # Jitter final pose of the box a little
            zpy.objects.jitter(
                obj,
                rotate_range=(
                    (0.0, 0.0),
                    (0.0, 0.0),
                    (-math.pi * 2, math.pi * 2),
                ),
            )

            if jitter_box_scale:
                # Jitter the scale of each box
                zpy.objects.jitter(
                    obj,
                    scale_range=(
                        (0.8, 1.2),
                        (0.8, 1.2),
                        (0.8, 1.2),
                    ),
                )

            if jitter_mesh:
                # Jitter (deform) the mesh of each box
                zpy.objects.jitter_mesh(
                    obj=obj,
                    scale=(
                        random.uniform(0.01, 0.03),
                        random.uniform(0.01, 0.03),
                        random.uniform(0.01, 0.03),
                    ),
                )

            if jitter_material:
                # Jitter the material (apperance) of each box
                for i in range(len(obj.material_slots)):
                    zpy.material.jitter(obj.material_slots[i].material)

        # Return camera to original position
        zpy.objects.restore_pose("Camera")

        # Jitter the camera pose
        zpy.objects.jitter(
            "Camera",
            translate_range=(
                (-2, 2),
                (-2, 2),
                (1, 3),  # Camera images are generally in this height range
            ),
        )

        # Return light to original position
        zpy.objects.restore_pose("Sun")

        # Jitter the light position
        zpy.objects.jitter(
            "Sun",
            translate_range=(
                (-5, 5),
                (-5, 5),
                (-5, 5),
            ),
        )
        bpy.data.objects["Sun"].data.energy = random.uniform(5, 15)

        # Pick a random hdri (from the local textures folder)
        zpy.hdris.random_hdri()

        # Name for each of the output images
        rgb_image_name = zpy.files.make_rgb_image_name(step_idx)
        iseg_image_name = zpy.files.make_iseg_image_name(step_idx)
        depth_image_name = zpy.files.make_depth_image_name(step_idx)

        zpy.render.render(
            rgb_path=saver.output_dir / rgb_image_name,
            iseg_path=saver.output_dir / iseg_image_name,
            depth_path=saver.output_dir / depth_image_name,
            # Randomize HSV for built-in data augmentation
            hsv=(
                random.uniform(0.4, 0.6),  # (hue)
                random.uniform(0.9, 1.2),  # (saturation)
                random.uniform(0.6, 1.3),  # (value)
            ),
        )

        # Add images to saver
        saver.add_image(
            name=rgb_image_name,
            style="default",
            output_path=saver.output_dir / rgb_image_name,
            frame=step_idx,
        )
        saver.add_image(
            name=iseg_image_name,
            style="segmentation",
            output_path=saver.output_dir / iseg_image_name,
            frame=step_idx,
        )
        saver.add_image(
            name=depth_image_name,
            style="depth",
            output_path=saver.output_dir / depth_image_name,
            frame=step_idx,
        )

        for obj in spawned_box_objects:
            # Add annotation to segmentation image
            saver.add_annotation(
                image=rgb_image_name,
                seg_image=iseg_image_name,
                seg_color=tuple(obj.seg.instance_color),
                category="box",
            )

        # Delete the spawned boxes
        zpy.objects.empty_collection(bpy.data.collections["SPAWNED"])

    # Write out annotations
    saver.output_annotated_images()
    saver.output_meta_analysis()

    # # ZUMO Annotations
    zpy.output_zumo.OutputZUMO(saver).output_annotations()

    # COCO Annotations
    zpy.output_coco.OutputCOCO(saver).output_annotations()

    log.info("Simulation complete.")


if __name__ == "__main__":

    # Set the logger levels
    zpy.logging.set_log_levels("info")

    # Parse the gin-config text block
    zpy.blender.parse_config("config")

    # Run the sim
    run()
