""" Crowd Sim.

Humans moving around in an HDRI.

"""
import logging
import random

import bpy
import gin
import mathutils
import zpy

log = logging.getLogger('zpy')


@gin.configurable('run')
@zpy.blender.save_and_revert
def run():
    """ Main run function.

    Any kwargs you put here will show up
    on the Data Portal. Give them types!
    """

    # Random seed results in unique behavior
    zpy.blender.set_seed()

    # Create the saver object
    saver = zpy.saver_image.ImageSaver(
        description='Crowd of humans.',
    )

    camera = bpy.data.objects["Camera"]

    # Make a list of humans and their keypoints
    human_collections = [
        bpy.data.collections['MOVING'],
        bpy.data.collections['IDLE'],
    ]
    humans = []
    keypoints = []
    for _human_collection in human_collections:
        for human in _human_collection.all_objects:
            humans.append(human)
            _keypoints = zpy.keypoints.Keypoints(
                root=bpy.data.objects[f'{human.name}_skeletonRoot'],
                style='coco',
                armature='anima',
            )
            keypoints.append(_keypoints)

    # Get all the subcategories for the humans
    _subcategories = []
    for human in humans:
        _subcategories.append(human.seg.instance_name)

    # Add the categories from the sim-level object
    _categories = bpy.context.scene.categories
    saver.add_category(
        name=_categories['person'].name,
        subcategories=_subcategories,
        color=tuple(_categories['person'].color),
        keypoints=keypoints[0].names,
        skeleton=keypoints[0].connectivity,
    )

    # Randomize the hdri
    zpy.hdris.random_hdri()

    # Run the sim.
    for step_idx in zpy.blender.step(
        start_frame=random.randint(0, 250),
    ):

        # Randomize the camera position
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
            name=cseg_image_name,
            style='segmentation',
            output_path=saver.output_dir / cseg_image_name,
            frame=step_idx,
        )
        saver.add_image(
            name=depth_image_name,
            style='depth',
            output_path=saver.output_dir / depth_image_name,
            frame=step_idx,
        )

        # Add annotations
        for i, human in enumerate(humans):
            # HACK Check that human head and feet are in view
            human_feet_position = human.matrix_world.to_translation()
            human_head_position = human.matrix_world.to_translation() + \
                mathutils.Vector((0.0, 0.0, 1.5))
            if zpy.camera.is_in_view(human_head_position, camera) or zpy.camera.is_in_view(human_feet_position, camera):
                # Update the keypoints
                keypoints[i].update()  # world_transform = human.matrix_world)
                saver.add_annotation(
                    image=rgb_image_name,
                    seg_image=iseg_image_name,
                    seg_color=tuple(human.seg.instance_color),
                    category=human.seg.category_name,
                    subcategory=human.seg.instance_name,
                    location=tuple(human.location),
                    # Keypoints
                    num_keypoints=keypoints[i].num_keypoints,
                    keypoints_xyv=keypoints[i].keypoints_xyv,
                    keypoints_xyz=keypoints[i].keypoints_xyz,
                    # MOT information (https://arxiv.org/pdf/2003.09003.pdf)
                    frame_id=step_idx,
                    mot_type=1,
                    person_id=i,
                )

    # Remap categories (this does nothing if not configured)
    saver.remap_filter_categories()

    # Write out annotations
    saver.output_annotated_images()
    saver.output_meta_analysis()

    # ZUMO Annotations
    zpy.output_zumo.OutputZUMO(saver).output_annotations()

    # COCO Annotations
    zpy.output_coco.OutputCOCO(saver).output_annotations()

    # MOT Annotations
    zpy.output_mot.OutputMOT(saver).output_annotations()

    log.info('Simulation complete.')


if __name__ == "__main__":

    # Set the logger levels
    zpy.logging.set_log_levels('info')

    # Parse the gin-config text block
    zpy.blender.parse_config('config')

    # Run the sim
    run()
