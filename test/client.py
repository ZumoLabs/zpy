import csv
import os
import random
import shutil
import unittest
from collections import defaultdict
from pathlib import Path
from pprint import pprint

import zpy.client as zpy
from zpy.client_util import remove_n_extensions, write_json


class TestClient(unittest.TestCase):
    def test_remove_n_extensions(self):
        self.assertTrue("/foo" == remove_n_extensions("/foo.rgb.png", 2))
        self.assertTrue("/images" == remove_n_extensions("/images.foo.rgb.png", 3))
        self.assertTrue("/images.rgb" == remove_n_extensions("/images.rgb.png", 1))
        self.assertTrue(
            "/foo/images" == remove_n_extensions("/foo/images.rgb.png", 9001)
        )

    def test_hash(self):
        dictA = hash({"foo": 1, "bar": 2})
        dictB = hash({"bar": 2, "foo": 1})
        self.assertEqual(hash(dictA), hash(dictB))
        self.assertEqual(hash(True), hash(True))
        self.assertNotEqual(hash(True), hash(False))
        self.assertNotEqual(hash(1), hash(2))
        self.assertNotEqual(hash([1]), hash([1, 1]))

    def test_preview(self):
        zpy.init(project_uuid="", auth_token="")
        dataset_config = zpy.DatasetConfig(sim_name="can_v7")
        dataset_config.set("run\\.padding_style", "square")
        previews = zpy.preview(dataset_config)
        pprint(previews)

    def test_generate(self):
        zpy.init(
            project_uuid="feb6e594-55e0-4f87-9e75-5a128221499f",
            auth_token="a4a13763b0dc0017b1fc9af890e9efea58fd072074ab9a169e5dcf0633310f28",
        )
        dataset_config = zpy.DatasetConfig("dumpster_v5.1")
        dataset_config.set("run\.padding_style", "messy")

        zpy.generate(dataset_config, num_datapoints=3)

    def test_generate_and_tvt_format_dataset(self):
        def dataset_callback(datapoints, categories, output_dir):
            if output_dir.exists():
                shutil.rmtree(output_dir)

            os.makedirs(output_dir / "train", exist_ok=True)
            os.makedirs(output_dir / "val", exist_ok=True)
            os.makedirs(output_dir / "test", exist_ok=True)

            metadata = {
                tvt_type: {"categories": {}, "images": {}, "annotations": []}
                for tvt_type in ["train", "val", "test"]
            }
            category_counts = {
                tvt_type: defaultdict(int) for tvt_type in ["train", "val", "test"]
            }

            for datapoint in datapoints:
                r = random.random()

                if r < 0.4:
                    tvt_type = "train"
                elif r < 0.8:
                    tvt_type = "test"
                else:
                    tvt_type = "val"

                # Annotations are stored by image_id so the dict update should not have any collisions
                annotations = datapoint["annotations"]
                metadata[tvt_type]["annotations"].update(annotations)

                images = datapoint["images"]
                for image_type, image in images.items():
                    old_image_name = Path(image["output_path"]).name
                    # Prefix old image name with the datapoint id to prevent naming collisions when moving directories
                    # and combining images from other datapoints
                    new_image_name = f'{datapoint["id"][:8]}.{old_image_name}'
                    new_path = output_dir / tvt_type / new_image_name

                    # Add the image and update the path to reflect its new location
                    metadata[tvt_type]["images"][image["id"]] = image
                    metadata[tvt_type]["images"][image["id"]]["output_path"] = str(new_path)

                    shutil.copy(image["output_path"], new_path)

                    # Add to the category counts for each annotation that this image has
                    for annotation in annotations[image["id"]]:
                        category_counts[tvt_type][annotation["category_id"]] += 1

                for category_id, category in categories.items():
                    metadata[tvt_type]["categories"][category_id] = {
                        **category,
                        "count": 0,
                    }

            for tvt_type in ["train", "val", "test"]:
                for category_id, count in category_counts[tvt_type].items():
                    metadata[tvt_type]["categories"][category_id]["count"] = count

                print(f"Writing {tvt_type} json...")
                path = output_dir / tvt_type / "annotations.json"
                blob = metadata[tvt_type]
                write_json(path, blob)

        zpy.init(
            project_uuid="feb6e594-55e0-4f87-9e75-5a128221499f",
            auth_token="12ea8d406b508be8fd0a1fef78f825440347fb10989536fcd1dedb9241327491",
        )
        dataset_config = zpy.DatasetConfig("dumpster_v5.1")
        dataset_config.set("run\.padding_style", "random")
        zpy.generate(
            dataset_config, num_datapoints=15, #  dataset_callback=dataset_callback
        )

    def test_generate_and_csv_format_dataset(self):
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
                row = (datapoint['id'], images['rgb']['output_path'], category_id)
                rows.append(row)

            # Write the rows to csv
            annotations_file_uri = str(output_dir / 'annotations.csv')
            with open(annotations_file_uri, 'w') as f:
                writer = csv.writer(f)
                columns = ['id', 'rgb_path', 'category_id']
                writer.writerow(columns)
                writer.writerows(rows)

        zpy.init(
            project_uuid="feb6e594-55e0-4f87-9e75-5a128221499f",
            auth_token="12ea8d406b508be8fd0a1fef78f825440347fb10989536fcd1dedb9241327491",
        )
        dataset_config = zpy.DatasetConfig("dumpster_v5.1")
        dataset_config.set("run\.padding_style", "random")
        zpy.generate(
            dataset_config, num_datapoints=15, #  dataset_callback=dataset_callback
        )
