### How to format your dataset with the dataset_callback parameter.

```python
# Make sure you're using the latest version of the zpy library:
#   pip install zpy-zumo --upgrade
import zpy.client as zpy
import shutil
import os
from collections import defaultdict
import random
import json

# We'll provide your project id during on-boarding
project_uuid = "..."

# This is your temporary auth token. It can be found by visiting:
#     https://app.zumolabs.ai/settings/auth-token
#
# The auth token will expire when you log out of the web app
auth_token = "..."

zpy.init(project_uuid=project_uuid, auth_token=auth_token)

# The simulation (sim) is the packaged version of the blender assets and
# generations script.
# 
# We'll give you the sim for your specific project and share new sim names when we
# create new versions.
sim_name = "demo_sim_v1"

# A DatasetConfig defines what synthetic data you want generated.
# 
# For now, there are no parameters to configure. But in the future, this will include
# sim specific parameters like: changing the cropping style or selecting which classes
# should be included in a dataset.
dataset_config = zpy.DatasetConfig(sim_name)

def dataset_callback(datapoints, categories, output_dir):
    """
    Example of using the dataset callback to split a dataset into train/val/test groups.
    
    See [zpy.client.default_dataset_callback][] for how the dataset is flattened by default.
    
    Args:
        datapoints (list): List of datapoints. See [zpy.client.default_dataset_callback][].
        categories (list): List of categories. See [zpy.client.default_dataset_callback][].
        output_dir (Path): Path of where dataset is output normally. You can use it or use something else.
    """
    # Remove the directory if it already exists
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Setup output directories
    os.makedirs(output_dir / "train", exist_ok=True)
    os.makedirs(output_dir / "val", exist_ok=True)
    os.makedirs(output_dir / "test", exist_ok=True)

    # Setup accumulator for categories, images, and annotations per split
    metadata = {
        tvt_type: {"categories": {}, "images": {}, "annotations": []}
        for tvt_type in ["train", "val", "test"]
    }
    
    # Setup accumulator for counting categories per split
    category_counts = {
        tvt_type: defaultdict(int) for tvt_type in ["train", "val", "test"]
    }

    # Loop over each datapoint in the dataset
    for datapoint in datapoints:
        images = datapoint["images"]
        annotations = datapoint["annotations"]

        # Assign the datapoint to a random split
        r = random.random()
        if r < 0.4:
            tvt_type = "train"
        elif r < 0.8:
            tvt_type = "test"
        else:
            tvt_type = "val"

        # Loop over each image in the datapoint to move it where you want it and
        # to assign it appropriate metadata based its new location.
        for image in images:
            # Assign new path
            new_path = output_dir / tvt_type / image["id"]

            # Copy to new location
            shutil.copy(image["output_path"], new_path)

            # Update image metadata in the accumulator
            metadata[tvt_type]["images"][image["id"]] = {
                **image,
                "output_path": str(new_path),
                "relative_path": image["id"],
                "name": image["id"],
            }

            # Find the annotations for this image
            filtered_annotations_by_image_id = [
                a for a in annotations if a["image_id"] == image["id"]
            ]
            
            # Accumulate the categories found in the annotations for this image
            for annotation in filtered_annotations_by_image_id:
                category_counts[tvt_type][annotation["category_id"]] += 1

        # Add annotations of this datapoint to the appropriate split
        metadata[tvt_type]["annotations"].extend(annotations)

        # Update metadata of categories. As they are passed in, the count is for the entire dataset
        for category in categories:
            metadata[tvt_type]["categories"][category["id"]] = {
                **category,
                "count": 0,
            }

    # Loop over each split
    for tvt_type in ["train", "val", "test"]:
        # Update the correct count that was accumulated
        for category_id, count in category_counts[tvt_type].items():
            metadata[tvt_type]["categories"][category_id]["count"] = count

        # Write the new annotation file
        path = output_dir / tvt_type / "annotations.json"
        blob = metadata[tvt_type]
        with open(path, "w") as outfile:
            json.dump(blob, outfile, indent=4)
    
# The generate call will cause our backend to actually generate a dataset. The dataset_callback will be used 
# after it has been generated and downloaded locally.
zpy.generate(dataset_config, num_datapoints=50, dataset_callback=dataset_callback)
```