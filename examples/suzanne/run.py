""" Suzanne Tutorial Scene. """

import bpy
import zpy

def run(num_images: int = 5):

    # Random seed results in unique behavior
    zpy.blender.set_seed()

    # Create the saver object
    saver = zpy.saver_image.ImageSaver(description='Suzannes from a camera view')

    # The monkey object
    suzanne = bpy.data.objects["Suzanne"]

    # Add the Suzzane category
    suzzane_seg_color = zpy.color.random_color(output_style='frgb')
    saver.add_category(
        name='Suzzane',
        color=tuple(suzzane_seg_color),
    )

    # Segment Suzzzane
    zpy.objects.segment(monkey, name='monkey', color=suzzane_seg_color)
    
    # Save the current camera position so we can jitter it later
    zpy.objects.save_pose(camera, "original_camera_pose")

    # Run the scene.
    for step_idx in zpy.blender.step(num_steps=num_images):

        # Jitter the camera position
        zpy.objects.restore_pose(bpy.data.objects["Camera"], "original_camera_pose")
        zpy.objects.jitter(bpy.data.objects["Camera"],
                    translate_range=((-0.02, 0.02), (-0.02, 0.02), (-0.02, 0.02)),
                    rotate_range=((-0.2, 0.2), (-0.2, 0.2), (-0.2, 0.2)))

        # Name for each of the output images
        rgb_image_name = zpy.files.make_rgb_image_name(step_idx)
        iseg_image_name = zpy.files.make_iseg_image_name(step_idx)
        depth_image_name = zpy.files.make_depth_image_name(step_idx)

        # Render image
        zpy.render.render_aov(
            rgb_path=saver.output_dir / rgb_image_name,
            iseg_path=saver.output_dir / iseg_image_name,
            depth_path=saver.output_dir / depth_image_name,
            width=640,
            height=480,
        )

        # Add images to saver
        saver.add_image(
            name=rgb_image_name,
            style='default',
            output_path=saver.output_dir / rgb_image_name,
            frame=step_idx,
            width=640,
            height=480,
        )
        saver.add_image(
            name=iseg_image_name,
            style='segmentation',
            output_path=saver.output_dir / iseg_image_name,
            frame=step_idx,
            width=640,
            height=480,
        )
        saver.add_image(
            name=depth_image_name,
            style='depth',
            output_path=saver.output_dir / depth_image_name,
            frame=step_idx,
            width=640,
            height=480,
        )

        # Add annotation to segmentation image
        saver.add_annotation(
            image=rgb_image_name,
            seg_image=iseg_image_name,
            seg_color=suzzane_seg_color,
            category="Suzzane",
        )

    # Write out annotations
    saver.output_annotated_images()
    saver.output_meta_analysis()

    # ZUMO Annotations
    zpy.output_zumo.OutputZUMO(saver).output_annotations()

    # COCO Annotations
    zpy.output_coco.OutputCOCO(saver).output_annotations()

if __name__ == "__main__":

    # Run the scene
    run()
