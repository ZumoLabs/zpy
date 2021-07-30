import json
import os
import random
import shutil
import unittest
from collections import defaultdict
from pathlib import Path

import zpy.client as zpy
from zpy.client_util import remove_n_extensions, format_dataset, write_json


def test_1(**init_kwargs):
    """In local env, simruns exist for config { "run.padding_style": "square" }"""
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig(sim_name="can_v7")
    dataset_config.set("run\\.padding_style", "square")
    print(dataset_config.config)
    previews = zpy.preview(dataset_config)
    urls = [preview["url"] for preview in previews]
    print(json.dumps(urls, indent=4, sort_keys=True))


def test_2(**init_kwargs):
    """In local env, simruns do NOT exist for config { "run.padding_style": "messy" }"""
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig("can_v7")
    dataset_config.set("run\\.padding_style", "messy")
    print(dataset_config.config)
    previews = zpy.preview(dataset_config)
    urls = [preview["url"] for preview in previews]
    print(json.dumps(previews, indent=4, sort_keys=True))
    print(json.dumps(urls, indent=4, sort_keys=True))


def pretty_print(object):
    try:
        json.dumps(object)
    except TypeError:
        print("Unable to serialize the object")
    else:
        print(json.dumps(object, indent=4))


def test_generate(**init_kwargs):
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig("can_v7")

    def datapoint_callback(images, annotations, categories):
        pretty_print(images)
        pretty_print(annotations)
        pretty_print(categories)

    dataset = zpy.generate(
        dataset_config,
        num_datapoints=39,
        materialize=True,
        # datapoint_callback=datapoint_callback
    )


# https://docs.python.org/3/library/unittest.html#module-unittest
class TestClientUtilMethods(unittest.TestCase):
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

    def test_generate(self):
        zpy.init(
            project_uuid="feb6e594-55e0-4f87-9e75-5a128221499f",
            auth_token="a4a13763b0dc0017b1fc9af890e9efea58fd072074ab9a169e5dcf0633310f28",
        )
        dataset_config = zpy.DatasetConfig("dumpster_v5.1")
        dataset_config.set("run\.padding_style", "messy")

        def datapoint_callback(images, annotations, categories):
            pretty_print(images)
            pretty_print(annotations)
            pretty_print(categories)

        zpy.generate(
            dataset_config, num_datapoints=3, datapoint_callback=datapoint_callback
        )

    def test_format_dataset(self):
        output_dir = Path("/home/korystiger/Downloads/ktest")
        if output_dir.exists():
            shutil.rmtree(output_dir)

        os.makedirs(output_dir / "train", exist_ok=True)
        os.makedirs(output_dir / "val", exist_ok=True)
        os.makedirs(output_dir / "test", exist_ok=True)

        metadata = {
            tvt_type: {"categories": {}, "images": {}, "annotations": []}
            for tvt_type in ["train", "val", "test"]
        }
        category_counts = {tvt_type: defaultdict(int) for tvt_type in ["train", "val", "test"]}

        def datapoint_callback(images, annotations, categories):
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

                filtered_annotations_by_image_id = [a for a in annotations if a['image_id'] == image['id']]
                for annotation in filtered_annotations_by_image_id:
                    category_counts[tvt_type][annotation['category_id']] += 1

            metadata[tvt_type]["annotations"].extend(annotations)

            for category in categories:
                metadata[tvt_type]["categories"][category["id"]] = category

        # format_dataset("/home/korystiger/Downloads/malibu-3k-0aac7584.zip",
        #     # datapoint_callback=datapoint_callback,
        # )
        # format_dataset('/home/korystiger/Downloads/can_v714-8c288ec8.zip',
        #                datapoint_callback=datapoint_callback)
        format_dataset('/home/korystiger/Downloads/trailer_empty_v5-f9b7ccb2.zip',
                       datapoint_callback=datapoint_callback)

        for tvt_type in ["train", "val", "test"]:
            for category_id, count in category_counts[tvt_type].items():
                metadata[tvt_type]['categories'][category_id]['count'] = count

            print(f"Writing {tvt_type} json...")
            path = str(output_dir / tvt_type / "annotations.json")
            blob = metadata[tvt_type]
            write_json(path, blob)


if __name__ == "__main__":
    unittest.main()
    # init_kwargs = {
    #     "base_url": "http://localhost:8000",
    #     "project_uuid": "aad8e2b2-5431-4104-a205-dc3b638b0dab",
    #     "auth_token": "214540cbd525f1ecf2bc52e2ddb7ef76801048e3f55aa4b33a9e501b115a736e",
    # }
    init_kwargs = {
        "base_url": "https://ragnarok.stage.zumok8s.org",
        "project_uuid": "feb6e594-55e0-4f87-9e75-5a128221499f",
        "auth_token": "a19f8a1cef0c1661f7de1fd513d740c499752fc567fc4c6fe6d11fdbce533b65",
    }
    # init_kwargs = {
    #     "base_url": "https://ragnarok.stage.zumok8s.org",
    #     "project_uuid": "91419af0-4815-41e7-9b77-5ef8154148c8",  # Compology
    #     "auth_token": "a51cacaa01082ba5237b49f74cd6ffa5cf88339345383d97bcadd1f99e5f9a01",
    # }
    # init_kwargs = {
    #     "base_url": "https://ragnarok.zumok8s.org",
    #     "project_uuid": "91419af0-4815-41e7-9b77-5ef8154148c8",  # Compology
    #     "auth_token": "7c1baae380c14a89b558a2fbf5f1c0ad923e61298c3ec87a0bdae6debbe549cb",
    # }
    # print("Running test_1:")
    # test_1(**init_kwargs)
    # print("Running test_2:")
    # test_2(**init_kwargs)
    # test format dataset

    # def datapoint_callback(images, annotations, categories):
    #     pretty_print(images)
    #     pretty_print(annotations)
    #     pretty_print(categories)

    # input_path = "/mnt/c/Users/georg/Zumo/Datasets/can_v714-8c288ec8.zip"
    # dataset_path = extract_zip(input_path)
    # format_dataset(dataset_path, datapoint_callback)

    # test_generate(**init_kwargs)
