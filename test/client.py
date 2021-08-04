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

    def test_generate_and_format_dataset(self):
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
                images = datapoint["images"]
                annotations = datapoint["annotations"]

                r = random.random()

                if r < 0.4:
                    tvt_type = "train"
                elif r < 0.8:
                    tvt_type = "test"
                else:
                    tvt_type = "val"

                for image in images:
                    new_path = output_dir / tvt_type / image["id"]

                    shutil.copy(image["output_path"], new_path)

                    metadata[tvt_type]["images"][image["id"]] = {
                        **image,
                        "output_path": str(new_path),
                        "relative_path": image["id"],
                        "name": image["id"],
                    }

                    filtered_annotations_by_image_id = [
                        a for a in annotations if a["image_id"] == image["id"]
                    ]
                    for annotation in filtered_annotations_by_image_id:
                        category_counts[tvt_type][annotation["category_id"]] += 1

                metadata[tvt_type]["annotations"].extend(annotations)

                for category in categories:
                    metadata[tvt_type]["categories"][category["id"]] = {
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
            dataset_config, num_datapoints=15, dataset_callback=dataset_callback
        )
