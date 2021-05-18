# What is a Sim?

A simulation, also known as "sim", is a scriptable 3D environment that is created using the zpy tools and Blender. A sim have the following principal components:

- `run.py` - The main script executed at runtime which creates and controls the 3D environment.
- `config.gin` - An optional configuration file which allows custom configuration at runtime.
- `main.blend` - The primary blenderfile which contains the run script. 

## Template Sim

We provide some template simulations as examples and for getting started quickly:

- [Package](https://zumolabs.github.io/zpy/zpy/example/package/): Detection and segmentation of packages/boxes
- [RPI](https://zumolabs.github.io/zpy/zpy/example/rpi/): Detection and segmentation of Raspberry Pi components 
- [Suzanne](https://zumolabs.github.io/zpy/zpy/example/part1/): Detection and segmentation of Suzanne monkey heads