""" RPI (Raspberry Pi) Sim.

Moves a camera around an RPI board centered around
the origin.

"""
import logging

import bpy
import gin
import zpy

log = logging.getLogger("zpy")


@gin.configurable("run")
@zpy.blender.save_and_revert
def run():
    """Main run function.

    Any kwargs you put here will show up
    on the Data Portal. Give them types!
    """

    # Random seed results in unique behavior
    zpy.blender.set_seed()

    # Create the saver object
    saver = zpy.saver_image.ImageSaver(
        description="Raspberry Pi component detection.",
    )

    camera = bpy.data.objects["Camera"]
    rpi_parts = {
        "rpi": bpy.data.collections["rpi"],
        "ethernet": bpy.data.collections["ethernet"],
        "pins": bpy.data.collections["pins"],
        "audio": bpy.data.collections["audio"],
    }

    # Add the categories from the scene-level object
    for category in bpy.context.scene.categories:
        saver.add_category(
            name=category.name,
            color=tuple(category.color),
        )

    # Run the sim.
    for step_idx in zpy.blender.step():

        # Random camera location
        zpy.objects.random_position_within_constraints(camera)

        # Name for each of the output images
        rgb_image_name = zpy.files.make_rgb_image_name(step_idx)
        iseg_image_name = zpy.files.make_iseg_image_name(step_idx)
        cseg_image_name = zpy.files.make_cseg_image_name(step_idx)
        depth_image_name = zpy.files.make_depth_image_name(step_idx)

        # Render image
        zpy.render.render(
            rgb_path=saver.output_dir / rgb_image_name,
            iseg_path=saver.output_dir / iseg_image_name,
            cseg_path=saver.output_dir / cseg_image_name,
            depth_path=saver.output_dir / depth_image_name,
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
            name=cseg_image_name,
            style="segmentation",
            output_path=saver.output_dir / cseg_image_name,
            frame=step_idx,
        )
        saver.add_image(
            name=depth_image_name,
            style="depth",
            output_path=saver.output_dir / depth_image_name,
            frame=step_idx,
        )

        # Add annotations
        for name, part in rpi_parts.items():
            # Add annotation to segmentation image
            saver.add_annotation(
                image=rgb_image_name,
                seg_image=iseg_image_name,
                seg_color=tuple(part.all_objects[0].seg.instance_color),
                category=name,
            )

        # This call creates correspondences between segmentation images
        # and the annotations. It should be used after both the images
        # and annotations have been added to the saver.
        saver.parse_annotations_from_seg_image(
            image_name=iseg_image_name,
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
