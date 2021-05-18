# Raspberry Pi (rpi)

The `rpi` [sim](https://zumolabs.github.io/zpy/zpy/tutorials/what_is_a_sim/) takes images from a varying camera viewpoint of a raspberry pi board in the middle of the scene. Sub-components of the rpi are individually [segmented](https://zumolabs.github.io/zpy/zpy/tutorials/segmentation/), and the resulting dataset is used for object detection or segmentation. This sim makes use of [Domain Randomization](https://zumolabs.github.io/zpy/overview/domain_randomization/).

![Example synthetic images from rpi sim.](https://github.com/ZumoLabs/zpy/raw/main/docs/assets/rpi_sim_synthetic.png)

![Example synthetic images from rpi sim.](https://github.com/ZumoLabs/zpy/raw/main/docs/assets/rpi_sim_dr.png)

## Blog

You can find the full blog post for this project [here](https://www.zumolabs.ai/post/training-ai-with-cgi).

## Code

The code for this example can be found [here](https://github.com/ZumoLabs/zpy/tree/main/examples/rpi)