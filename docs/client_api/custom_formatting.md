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
    Example of using dataset_callback to format a dataset into CSV format.
    
    See [zpy.client.default_dataset_callback][] for how the dataset is flattened by default.
    
    Args:
        datapoints (list): List of datapoints. See [zpy.client.default_dataset_callback][].
        categories (dict): Dict of category_id to Category. See [zpy.client.default_dataset_callback][].
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
        # Dict of image_type to image 
        images = datapoint['images']
        
        # Get annotations via the image id
        rgb_annotations = datapoint['annotations'][images['rgb']['id']]
        # iseg_annotations = datapoint['annotations'][images['iseg']['id']]
        
        # The Sim design determines the annotation intrinsics. In this example we know there is only
        # one annotation per datapoint, but there could be all sorts of interesting metadata here!
        category_id = rgb_annotations[0]['category_id']
        
        # Lookup category information if you need it
        # category = categories[category_id]
        
        # Accumulate new row
        row = (datapoint['id'], images['rgb']['output_path'], images['iseg']['output_path'], category_id)
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