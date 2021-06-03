""" Suzanne Tutorial Sim: Part 3. """

import logging
import math
import random

import bpy

import zpy

log = logging.getLogger("zpy")


def run():
    # Random seed results in unique behavior
    zpy.blender.set_seed()

    # Create the saver object
    saver = zpy.saver_image.ImageSaver(description="Domain randomized Suzanne")

    # Add the Suzanne category
    suzanne_seg_color = zpy.color.random_color(output_style="frgb")
    saver.add_category(name="Suzanne", color=suzanne_seg_color)

    # Segment Suzzanne (make sure a material exists for the object!)
    zpy.objects.segment("Suzanne", color=suzanne_seg_color)

    # Save the positions of objects so we can jitter them later
    zpy.objects.save_pose("Camera", "cam_pose")
    zpy.objects.save_pose("Suzanne", "suzanne_pose")

    # Run the sim.
    for step_idx in zpy.blender.step():
        # Example logging
        log.info("This is an info log")
        log.debug("This is a debug log")

        # Return camera and Suzanne to original positions
        zpy.objects.restore_pose("Camera", "cam_pose")
        zpy.objects.restore_pose("Suzanne", "suzanne_pose")

        # Jitter Suzane pose
        zpy.objects.jitter(
            "Suzanne",
            translate_range=((-5, 5), (-5, 5), (-5, 5)),
            rotate_range=(
                (-math.pi, math.pi),
                (-math.pi, math.pi),
                (-math.pi, math.pi),
            ),
        )

        # Jitter the camera pose
        zpy.objects.jitter(
            "Camera",
            translate_range=(
                (-5, 5),
                (-5, 5),
                (-5, 5),
            ),
        )

        # Camera should be looking at Suzanne
        zpy.camera.look_at("Camera", bpy.data.objects["Suzanne"].location)

        # HDRIs are like a pre-made background with lighting
        zpy.hdris.random_hdri()

        # Pick a random texture from the 'textures' folder (relative to blendfile)
        # Textures are images that we will map onto a material
        new_mat = zpy.material.random_texture_mat()
        zpy.material.set_mat("Suzanne", new_mat)

        # Have to segment the new material
        zpy.objects.segment("Suzanne", color=suzanne_seg_color)

        # Jitter the Suzanne material
        zpy.material.jitter(bpy.data.objects["Suzanne"].active_material)

        # Jitter the HSV for empty and full images
        hsv = (
            random.uniform(0.49, 0.51),  # (hue)
            random.uniform(0.95, 1.1),  # (saturation)
            random.uniform(0.75, 1.2),  # (value)
        )

        # Name for each of the output images
        rgb_image_name = zpy.files.make_rgb_image_name(step_idx)
        iseg_image_name = zpy.files.make_iseg_image_name(step_idx)
        depth_image_name = zpy.files.make_depth_image_name(step_idx)

        # Render image
        zpy.render.render(
            rgb_path=saver.output_dir / rgb_image_name,
            iseg_path=saver.output_dir / iseg_image_name,
            depth_path=saver.output_dir / depth_image_name,
            hsv=hsv,
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

        # Add annotation to segmentation image
        saver.add_annotation(
            image=rgb_image_name,
            seg_image=iseg_image_name,
            seg_color=suzanne_seg_color,
            category="Suzanne",
        )

    # Write out annotations
    saver.output_annotated_images()
    saver.output_meta_analysis()

    # ZUMO Annotations
    zpy.output_zumo.OutputZUMO(saver).output_annotations()

    # COCO Annotations
    zpy.output_coco.OutputCOCO(saver).output_annotations()


if __name__ == "__main__":
    # Set the logger levels
    zpy.logging.set_log_levels("info")

    # Parse the gin-config text block
    zpy.blender.parse_config("config")

    # Run the sim
    run()
