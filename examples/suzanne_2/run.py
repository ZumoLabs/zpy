""" Suzanne Tutorial Scene: Part 2. """

import bpy
import zpy
import logging

import gin
import math

log = logging.getLogger('zpy')


def run():

    # Random seed results in unique behavior
    zpy.blender.set_seed()

    # Create the saver object
    saver = zpy.saver_image.ImageSaver(
        description='Suzannes from a camera view')

    # Add the Suzanne category
    suzanne_seg_color = zpy.color.random_color(output_style='frgb')
    saver.add_category(name='Suzanne', color=suzanne_seg_color)

    # Segment Suzzanne (make sure a material exists for the object!)
    zpy.objects.segment(
        bpy.data.objects["Suzanne"], name='Suzanne', color=suzanne_seg_color)

    # Save the current camera position so we can jitter it later
    zpy.objects.save_pose(bpy.data.objects["Camera"], "original_camera_pose")

    # Save the current suzanne position so we can jitter it later
    zpy.objects.save_pose(bpy.data.objects["Suzanne"], "original_suzanne_pose")

    # Run the scene.
    for step_idx in zpy.blender.step():
        
        # Example logging
        log.info('This is an info log')
        log.debug('This is a debug log')

        # Jitter the camera pose
        zpy.objects.restore_pose(
            bpy.data.objects["Camera"], "original_camera_pose")
        zpy.objects.jitter(
            bpy.data.objects["Camera"],
            translate_range=(
                (-0.02, 0.02),
                (-0.02, 0.02),
                (-0.02, 0.02),
            ),
            rotate_range=(
                # In radians
                (-0.2, 0.2),
                (-0.2, 0.2),
                (-0.2, 0.2),
            ))

        # Jitter Suzane pose
        zpy.objects.restore_pose(
            bpy.data.objects["Suzanne"], "original_suzanne_pose")
        zpy.objects.jitter(
            bpy.data.objects["Suzanne"],
            translate_range=(
                (-0.02, 0.02),
                (-0.02, 0.02),
                (-0.02, 0.02)),
            rotate_range=(
                (-math.pi, math.pi),
                (-math.pi, math.pi),
                (-math.pi, math.pi),
            ))

        # Name for each of the output images
        rgb_image_name = zpy.files.make_rgb_image_name(step_idx)
        iseg_image_name = zpy.files.make_iseg_image_name(step_idx)
        depth_image_name = zpy.files.make_depth_image_name(step_idx)

        # Render image
        zpy.render.render_aov(
            rgb_path=saver.output_dir / rgb_image_name,
            iseg_path=saver.output_dir / iseg_image_name,
            depth_path=saver.output_dir / depth_image_name,
        )

        # Add images to saver
        saver.add_image(
            name=rgb_image_name,
            style='default',
            output_path=saver.output_dir / rgb_image_name,
            frame=step_idx,
        )
        saver.add_image(
            name=iseg_image_name,
            style='segmentation',
            output_path=saver.output_dir / iseg_image_name,
            frame=step_idx,
        )
        saver.add_image(
            name=depth_image_name,
            style='depth',
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
    zpy.logging.set_log_levels('debug')

    # Parse the gin-config text block
    zpy.blender.parse_config('config')

    # Run the scene
    run()
