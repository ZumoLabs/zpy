import json
from os import listdir
from os.path import join
from os.path import splitext
import os
import shutil
import re
import zipfile
from pathlib import Path
from typing import Union
from itertools import groupby
import uuid

import zpy.client as zpy


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


def process_zipped_dataset(path_to_zipped_dataset, datapoint_callback=None):
    def remove_n_extensions(path: Union[str, Path], n: int = 1) -> Path:
        p = Path(path)
        extensions = "".join(p.suffixes[-n:])  # remove n extensions
        return str(p).removesuffix(extensions)

    def unzip_to_path(path_to_zip: Union[str, Path], output_path: Union[str, Path]):
        with zipfile.ZipFile(path_to_zip, "r") as zip_ref:
            zip_ref.extractall(output_path)

    unzipped_dataset_path = Path(remove_n_extensions(path_to_zipped_dataset, n=1))
    unzip_to_path(path_to_zipped_dataset, unzipped_dataset_path)
    output_dir = join(
        unzipped_dataset_path.parent, unzipped_dataset_path.name + "_formatted"
    )

    def preprocess_datapoints(unzipped_dataset_path, datapoint_callback):
        """
        Calls datapoint_callback(images: [{}], annotations: [{}], categories: [{}]) once per datapoint.
        """

        # batch level
        for batch in listdir(unzipped_dataset_path):
            BATCH_UUID = str(uuid.uuid4())
            batch_uri = join(unzipped_dataset_path, batch)
            annotation_file_uri = join(batch_uri, "_annotations.zumo.json")
            metadata = json.load(open(annotation_file_uri))
            batch_images = list(dict(metadata["images"]).values())
            # https://www.geeksforgeeks.org/python-identical-consecutive-grouping-in-list/
            images_grouped_by_datapoint = [
                list(y)
                for x, y in groupby(
                    batch_images,
                    lambda x: remove_n_extensions(Path(x["relative_path"]), n=2),
                )
            ]

            # datapoint level
            for images in images_grouped_by_datapoint:
                DATAPOINT_UUID = str(uuid.uuid4())

                # get [images], [annotations], [categories] per data point
                image_ids = [i["id"] for i in images]
                annotations = [
                    a for a in metadata["annotations"] if a["image_id"] in image_ids
                ]
                category_ids = list(set([a["category_id"] for a in annotations]))
                categories = [
                    c
                    for c in list(dict(metadata["categories"]).values())
                    if c["id"] in category_ids
                ]

                # functions that take ids and return new ones
                def mutate_category_id(category_id: Union[str, int]) -> str:
                    return {
                        str(c["id"]): (str(c["id"]) + "-" + BATCH_UUID)
                        for c in categories
                    }[str(category_id)]

                def mutate_image_id(image_id: Union[str, int]) -> str:
                    return {
                        str(img["id"]): str(
                            DATAPOINT_UUID
                            + "-"
                            + str(Path(img["name"]).suffixes[-2]).replace(".", "")
                        )
                        for img in images
                    }[str(image_id)]

                # mutate the arrays
                images_mutated = [
                    {
                        **i,
                        "output_path": join(batch_uri, Path(i["relative_path"])),
                        "id": mutate_image_id(i["id"]),
                    }
                    for i in images
                ]
                annotations_mutated = [
                    {
                        **a,
                        "category_id": mutate_category_id(a["category_id"]),
                        "image_id": mutate_image_id(a["image_id"]),
                    }
                    for a in annotations
                ]
                categories_mutated = [
                    {**c, "id": mutate_category_id(c["id"])} for c in categories
                ]

                # call the callback with the mutated arrays
                datapoint_callback(
                    images_mutated, annotations_mutated, categories_mutated
                )

    # call the callback if provided
    if datapoint_callback is not None:
        preprocess_datapoints(unzipped_dataset_path, datapoint_callback)

    # if no callback provided -  use default json accumulator, write out json, rename and copy images to new folder
    else:
        accumulated_metadata = {"images": [], "annotations": [], "categories": []}

        def default_datapoint_callback(images, annotations, categories):
            # accumulate json
            accumulated_metadata["annotations"].extend(annotations)
            accumulated_metadata["categories"].extend(categories)

            for image in images:
                # reference original path to save from
                original_image_uri = image["output_path"]

                # build new path
                image_extensions = "".join(Path(image["name"]).suffixes[-2:])
                datapoint_uuid = "-".join(str(image["id"]).split("-")[:-1])
                new_image_name = datapoint_uuid + image_extensions
                output_image_uri = join(output_dir, Path(new_image_name))

                # add to accumulator
                image = {
                    **image,
                    "name": new_image_name,
                    "output_path": output_image_uri,
                    "relative_path": new_image_name,
                }
                accumulated_metadata["images"].append(image)

                # copy image to new folder
                try:
                    shutil.copy(original_image_uri, output_image_uri)
                except IOError as io_err:
                    os.makedirs(os.path.dirname(output_image_uri))
                    shutil.copy(original_image_uri, output_image_uri)

        preprocess_datapoints(unzipped_dataset_path, default_datapoint_callback)

        # https://www.geeksforgeeks.org/python-removing-duplicate-dicts-in-list/
        unique_elements_metadata = {
            k: [i for n, i in enumerate(v) if i not in v[n + 1 :]]
            for k, v in accumulated_metadata.items()
        }
        # write json
        metadata_output_path = join(output_dir, Path("_annotations.zumo.json"))
        try:
            with open(metadata_output_path, "w") as outfile:
                json.dump(unique_elements_metadata, outfile)
        except IOError as io_err:
            os.makedirs(os.path.dirname(metadata_output_path))
            with open(metadata_output_path, "w") as outfile:
                json.dump(unique_elements_metadata, outfile)


def test_generate():
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig("can_v7")

    def datapoint_callback(images, annotations, categories):
        pretty_print(images)
        pretty_print(annotations)
        pretty_print(categories)

    dataset = zpy.generate(
        dataset_config,
        num_datapoints=30,
        # materialize=True,
        # datapoint_callback=datapoint_callback
    )


if __name__ == "__main__":
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

    # input_path = "/mnt/c/Users/georg/Zumo/Datasets/can_v714-8c288ec8.zip"
    # process_zipped_dataset(input_path)

    test_generate()
