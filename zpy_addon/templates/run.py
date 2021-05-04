""" This is a run script. """
import logging

import bpy
import gin
import zpy

log = logging.getLogger("zpy")


@gin.configurable("run")
def run(
    # Add any kwargs here that you want
    boolkwarg: bool = True,
    intkwarg: int = 5,
    mysterykwarg="foo",
):
    """Main run function.

    Any kwargs you put here will show up
    on the Data Portal as configurable parameters.
    Give them types and defaults!
    """

    log.info("Inside the run() function! The values of the config kwargs are:")
    log.info(f"boolkwarg {boolkwarg}")
    log.info(f"intkwarg {intkwarg}")
    log.info(f"mysterykwarg {mysterykwarg}")

    # You can use any bpy function call here
    log.info(f'Objects in the scene: {bpy.data.objects}')

    # Random seed results in unique behavior
    zpy.blender.set_seed()

    # Create the saver object
    saver = zpy.saver_image.ImageSaver(description="Suzannes from a camera view")

    # This assumes you have a "Suzanne" object in your Blender scene

    # Add the Suzanne category
    suzanne_seg_color = zpy.color.random_color(output_style="frgb")
    saver.add_category(name="Suzanne", color=suzanne_seg_color)

    # Segment Suzzanne (make sure a material exists for the object!)
    zpy.objects.segment("Suzanne", color=suzanne_seg_color)

    # Run the sim.
    for step_idx in zpy.blender.step():

        # Use different logging levels for more detailed printouts
        log.info("This is an info log")
        log.debug("This is a debug log")

        # Name for each of the output images
        rgb_image_name = zpy.files.make_rgb_image_name(step_idx)
        iseg_image_name = zpy.files.make_iseg_image_name(step_idx)

        # Render image
        zpy.render.render(
            rgb_path=saver.output_dir / rgb_image_name,
            iseg_path=saver.output_dir / iseg_image_name,
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

    log.info("Simulation complete.")


if __name__ == "__main__":

    # Set the logger levels
    zpy.logging.set_log_levels("info")

    # Parse the gin-config text block
    zpy.blender.parse_config("config")

    # Run the sim
    run()
