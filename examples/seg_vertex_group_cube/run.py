""" Uses default cube to show segmentation using vertex groups. """

import logging
from pathlib import Path

import bpy
import zpy

log = logging.getLogger("zpy")


def run():

    # The default cube when you open a new Blender file
    cube = bpy.data.objects["Cube"]

    # Random boiler plate required to render out images
    zpy.material.make_aov_material_output_node(obj=cube, style="category")
    cube.data.sculpt_vertex_colors.new(name="category")

    # Make some random segmentation colors
    segmentation_color_a = zpy.color.random_color(output_style="frgba")
    segmentation_color_b = zpy.color.random_color(output_style="frgba")

    # Cubes have 8 vertices, split it into two vertex groups
    cube.vertex_groups.new(name="sideA").add([0, 1, 4, 5], weight=1.0, type="ADD")
    cube.vertex_groups.new(name="sideB").add([2, 3, 6, 7], weight=1.0, type="ADD")

    for vertex in cube.data.vertices:
        # Color half the cube one color
        if cube.vertex_groups["sideA"].index == vertex.groups[0].group:
            cube.data.sculpt_vertex_colors["category"].data[
                vertex.index
            ].color = segmentation_color_a
        # and the other one the other color
        elif cube.vertex_groups["sideB"].index == vertex.groups[0].group:
            cube.data.sculpt_vertex_colors["category"].data[
                vertex.index
            ].color = segmentation_color_b

    # Render out an image
    zpy.render.render(
        rgb_path=Path("/tmp/output/color_image.png"),
        cseg_path=Path("/tmp/output/segmentation_image.png"),
    )


if __name__ == "__main__":

    # Set the logger levels
    zpy.logging.set_log_levels("info")

    # Run the sim
    run()
