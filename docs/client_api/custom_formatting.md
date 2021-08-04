### How to format your dataset with the dataset_callback parameter.

```python
import zpy.client as zpy
import os
import shutil
from pathlib import Path
import csv

project_uuid = "..."
auth_token = "..."
zpy.init(project_uuid=project_uuid, auth_token=auth_token)
sim_name = "demo_sim_v1"
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
    # The default location is passed in, but you can change it to whatever you want
    output_dir = Path('/tmp/output_dir')
    if output_dir.exists():
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Define row accumulator
    rows = []
    # Loop over datapoints to build rows
    for datapoint in datapoints:
        # Loop over images in datapoint to find the ones we need
        images = datapoint['images']
        rgb_image, iseg_image = {}, {}
        for image in images:
            if image['name'].endswith('.rgb.png'):
                rgb_image = image
            elif image['name'].endswith('.iseg.png'):
                iseg_image = image
            else:
                # There could be other images here but we've decided we only care about
                # rgb and iseg for this example.
                pass
        
        # Update the image paths to where we want them, we could leave them unchanged too    
        new_rgb_path = output_dir / rgb_image['name']
        new_iseg_path = output_dir / iseg_image['name'] 
        shutil.copy(rgb_image["output_path"], new_rgb_path)
        shutil.copy(iseg_image["output_path"], new_iseg_path)
        
        # We know each datapoint will only have 1 category as per the Sim design
        annotations = datapoint['annotations']
        category_id = annotations[0]['category_id']
        
        # Accumulate new row
        row = (datapoint['id'], new_rgb_path, new_iseg_path, category_id)
        rows.append(row)
    
    # Write the rows to csv
    annotations_file_uri = str(output_dir / 'annotations.csv')
    with open(annotations_file_uri, 'w') as f:
        writer = csv.writer(f)
        columns = ['id', 'rgb_path', 'iseg_path', 'category_id']
        writer.writerow(columns)
        writer.writerows(rows)
    
# The generate call will cause our backend to actually generate a dataset. The dataset_callback will be used 
# after it has been generated and downloaded locally.
zpy.generate(dataset_config, num_datapoints=50, dataset_callback=dataset_callback)
```