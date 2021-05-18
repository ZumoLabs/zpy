# Package

The `package` [sim](https://zumolabs.github.io/zpy/zpy/tutorials/what_is_a_sim/) spawns packages on a floor and takes images from a varying camera viewpoint. Boxes are individually [segmented](https://zumolabs.github.io/zpy/zpy/tutorials/segmentation/), and the resulting dataset is used for object detection.

![Example synthetic images from package sim.](https://github.com/ZumoLabs/zpy/raw/main/docs/assets/package_sim_boxes.png)

## Results

We trained a CNN on synthetic data produced by this sim. Below are images showing predictions from this network:

![Results from model trained on package sim dataset.](https://github.com/ZumoLabs/zpy/raw/main/docs/assets/package_sim_results.png)

## Blog

You can find the full blog post for this project [here]().

## Code

The code for this example can be found [here](https://github.com/ZumoLabs/zpy/tree/main/examples/package).