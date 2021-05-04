""" Suzanne Tutorial Sim. """

import zpy


def run(num_images: int = 5):

    # Random seed results in unique behavior
    zpy.blender.set_seed()

    # Create the saver object
    saver = zpy.saver_image.ImageSaver(description="Suzannes from a camera view")

    # Add the Suzanne category
    suzanne_seg_color = zpy.color.random_color(output_style="frgb")
    saver.add_category(name="Suzanne", color=suzanne_seg_color)

    # Segment Suzzanne (make sure a material exists for the object!)
    zpy.objects.segment("Suzanne", color=suzanne_seg_color)

    # Run the sim.
    for step_idx in zpy.blender.step(num_steps=num_images):

        # Name for each of the output images
        rgb_image_name = zpy.files.make_rgb_image_name(step_idx)
        iseg_image_name = zpy.files.make_iseg_image_name(step_idx)

        # Render image
        zpy.render.render(
            rgb_path=saver.output_dir / rgb_image_name,
            iseg_path=saver.output_dir / iseg_image_name,
            width=640,
            height=480,
        )

        # Add images to saver
        saver.add_image(
            name=rgb_image_name,
            style="default",
            output_path=saver.output_dir / rgb_image_name,
            frame=step_idx,
            width=640,
            height=480,
        )
        saver.add_image(
            name=iseg_image_name,
            style="segmentation",
            output_path=saver.output_dir / iseg_image_name,
            frame=step_idx,
            width=640,
            height=480,
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

    # Run the sim
    run()
