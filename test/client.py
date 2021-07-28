import json

import zpy.client as zpy
from zpy.client_util import extract_zip, format_dataset, hash

import unittest
from zpy.client_util import remove_n_extensions
from numpy import array_equal

from zpy.client import DatasetConfig


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


def test_3(**init_kwargs):
    """"""
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig("dumpster_v2")
    # dataset_config.set("run\\.padding_style", "square")
    zpy.generate("dumpster_v2.21", dataset_config, num_datapoints=3, materialize=True)


def pretty_print(object):
    try:
        json.dumps(object)
    except TypeError:
        print("Unable to serialize the object")
    else:
        print(json.dumps(object, indent=4))


def test_generate(**init_kwargs):
    print("hey")

    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig("can_v7")

    def datapoint_callback(images, annotations, categories):
        pretty_print(images)
        pretty_print(annotations)
        pretty_print(categories)

    dataset = zpy.generate(
        dataset_config,
        num_datapoints=37,
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


if __name__ == "__main__":
    # unittest.main()
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
    # print("Running test_3:")
    # test_3(**init_kwargs)
    # test format dataset

    def datapoint_callback(images, annotations, categories):
        pretty_print(images)
        pretty_print(annotations)
        pretty_print(categories)

    # input_path = "/mnt/c/Users/georg/Zumo/Datasets/can_v714-8c288ec8.zip"
    # dataset_path = extract_zip(input_path)
    # format_dataset(dataset_path)

    # test_generate(**init_kwargs)

