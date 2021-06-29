# Script Writing Guide

This guide gives you pointers and tips for writing a zpy run script. It is not meant to completely cover every single instance, but these things should be similar or the same over all sims.

## Blender File Setup

In terms of actually setting the file up, you don’t need a strict Collection Hierarchy, because it’s so much easier to write the code and then vary the structure of the `*.blend` file as you change things over a project's lifecycle. Put like objects with like objects, for example: lights can be named and put in a collection with other lights that need similar functions enacted upon them. Collections and objects should be named with clarity in mind. Anyone should be able to discern what is in the sim by looking at the named objects.

## Imports

Imports are flexible and should be added as needed, in general every run script should have the following imports:

```
import bpy
import zpy
import logging
```

## Logging

Use the zpy logger object, which uses Python's logging module

```
log = logging.getLogger('zpy')
        
log.info('This is an info log')
log.debug('This is a debug log')
```

You can set the log levels as such:

```
zpy.logging.set_log_levels('debug')
```

## Decorators

These decorators on the run function have different purposes, `@gin.configurable('run')` allows you to configure run function kwargs with gin. `@zpy.blender.save_and_revert` will save and revert the `*.blend` file every time you run it, allowing for local debugging.

## Run Kwargs

The keyword arguments (kwargs) for the run function will be exposed to the end user. Figure out which configs are most useful for your project so you can toggle and change values when generating in the cloud. An example of run kwargs:

```
def run(
    random_floor_tex: bool = True,
    jitter_mesh: bool = False,
    jitter_scale: bool = False,
    jitter_material: bool = False,
    use_distractors: bool = True,
):
```

## Seed

Set the random seed to have repeatably random behavior.

```
zpy.blender.set_seed(seed=43)
```

## Saving data

Saver objects allow us to store all the metadata and annotations for the data we’re generating. You can create one with this call:

```
saver = zpy.saver_image.ImageSaver(
    description='description',
)
```

## Creating Segmentation Colors

Create a segmentation color for each category and segment any objects:

```
category_A_segmentation_color = zpy.color.random_color(output_style='frgb')

saver.add_category(
        name='category_A',
        color=category_A_segmentation_color,
)

zpy.objects.segment('object_name',
    color=category_A_segmentation_color, as_category=True, as_single=True)
```

## Saving Pose

Save and restore the position of objects in the sim before each step.

```
zpy.objects.save_pose('Camera')

for frame in zpy.blender.step():
    zpy.objects.restore_pose('Camera')
```

## Lighting

Lighting can be added to a `ILLUMINATION` collection, inside the World Set up. 
Save lighting as a list, or iterate over the lighting using the `bpy.data.Lighting` type, this means the actual lighting within the scene can be changed or refactored without changing the script. If at all possible, do not reference objects by name, add them to the list and then manipulate that way. 

```
lighting = []
for obj in zpy.objects.for_obj_in_collections([
    bpy.data.collections['ILLUMINATION']
]):
    lighting.append(obj)
```

## The Loop

Use frame as the iterator variable 

```
# Setup things
for frame in zpy.blender.step():
    # Do things
```

## Objects

Restore pose of objects if needed. Then jitter. Jitter the mesh (slighty tweaks the points of the mesh), jitter the scale, jitter the rotation, jitter the position of the object. Always use ‘if’ logic to be able to turn the jitter on and off in the kwargs. 
Example:


Following the logic of trying to work on things in lists for flexibility rather than naming specific objects, putting objects that need similar operations performed on them into Collections is useful. If all the objects you’re using are Distractors that need to be randomly distributed around a zone, put them in the same Collection. Another option provided by Blender is the ability to filter by name. This allows us to create new objects or copy existing objects and then as long as the appropriate string is in their name, they’ll work without changing the script. The last way of referring to objects without using their name is with a Type. If we want to change all the lighting for example, we could use: for obj in bpy.data.light: to get all the lights.  

## Materials

Jitter materials. There are three main types of material jitter, moving the material around a little, picking an entire random texture and randomly changing the material properties of a shader. Again, use IF logic to be able to switch these effects on and off with a bool.

## Object Distribution and Spawning

To place items in a space, we can use a spawning algorithm written in python, which will vary depending on the needs of the sim. Another way to get native spawning inside of Blender is to use Geometry Nodes. This workflow isn’t perfect, but it can save some time trying to figure out our own spawning methods. 

- Add a new Geometry Node System with a Point Distribute and Point Instance Node. 
- Randomize the locations of objects or objects within a Collection by linking seed value to frame. 
- Turn off the Render Flag of the Spawner. 
- Use `zpy.select` to select Spawner. 
- Use “Make Instances Real” to create separate instances, then make each object a single user. 
- Move the object to a separate Collection to isolate them. 
- Loop through spawned objects to segment them as individual objects. 
- Use if `obj.name` to apply category segments.  
- Randomize the objects further as desired. 
- Delete spawned instances of an object. 

A lot of these ending commands will be the same regardless of what sim you’re working on, as they involve saving and output the images, which is similar between most sims. 

# Rendering

To render out images, first decide on names for the images.

```
rgb_image_name = zpy.files.make_rgb_image_name(frame)
iseg_image_name = zpy.files.make_iseg_image_name(frame)
```

This call will actually render the images to file.

```
zpy.render.render(
    rgb_path=saver.output_dir / rgb_image_name,
    iseg_path=saver.output_dir / iseg_image_name,
    width=image_width,
    height=image_height,
)
```

Then add images to saver:

```
saver.add_image(
    name=rgb_image_name,
    style='default',
    output_path=saver.output_dir / rgb_image_name,
    frame=frame,
    width=image_width,
    height=image_height,
)
saver.add_image(
    name=iseg_image_name,
    style='segmentation',
    output_path=saver.output_dir / iseg_image_name,
    frame=frame,
    width=image_width,
    height=image_height,
)
```

# Annotations

After working to randomize the scene, we need to add annotations to the scene. We have found it’s easier to use `name` to filter through objects, but type or collection is a valid way of adding annotations. 

Example of using name to add a bounding box annotation: 

```
if 'box.' in obj.name:
    saver.add_annotation(
        image=rgb_image_name,
        seg_image=iseg_image_name,
        seg_color=tuple(obj.seg.instance_color),
        category=obj.seg.category_name,
    )
```

Writing out annotations with a populated saver object:

```
zpy.output_zumo.OutputZUMO(saver).output_annotations()
zpy.output_coco.OutputCOCO(saver).output_annotations()
```