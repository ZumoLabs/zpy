import json
from os import listdir
from os.path import join
from os.path import splitext
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
    zpy.generate("dumpster_v2.21", dataset_config,
                 num_datapoints=3, materialize=True)


# def is_image(path: Union[str, Path]) -> bool:
#     '''
#     https://www.geeksforgeeks.org/how-to-validate-image-file-extension-using-regular-expression/
#     https://realpython.com/regex-python/
#     '''
#     img_regex = "(?i)([^\\s]+(\\.(jpe?g|png|gif|bmp))$)"
#     pattern = re.compile(img_regex)
#     return re.search(pattern, path)


def default_saver_func(image_uris, metadata):

    images = list(dict(metadata["images"]).values())

    for uri in image_uris:
        image = next((i for i in images if i["name"] in uri), None)

        if image is not None:
            image_id = image['id']
            image_name = image['name']

            annotation = next(
                (a for a in metadata["annotations"]
                 if a["image_id"] == image_id), None
            )

            batch_name = Path(
                str(image['output_path'])
                .removesuffix(str(image['relative_path']))
            ).name

            unzipped_path = Path(
                str(uri)
                .removesuffix(str(image['relative_path']))
            ).parent

            default_output_path = join(
                unzipped_path.parent,
                unzipped_path.name + "_formatted"
            )

            uuid.uuid4()

            output_file_uri = join(
                default_output_path,
                category_label
                + "-"
                + batch_name[:4]
                + "-"
                + image_name
                + ".jpg",
            )
            shutil.copy(image, output_file_uri)

            # if annotation is not None:
            #     category_id = str(annotation["category_id"])
            #     category_label = metadata["categories"][category_id]["name"]

            #     output_file_uri = join(
            #         default_output_path,
            #         category_label
            #         + "-"
            #         + batch_name[:4]
            #         + "-"
            #         + image_name
            #         + ".jpg",
            #     )
            #     shutil.copy(image, output_file_uri)


def format_dataset(path_to_zipped_dataset, saver_func):

    def remove_n_extensions(path: Union[str, Path], n: int = 1) -> Path:
        p = Path(path)
        extensions = "".join(p.suffixes[-n:])  # remove n extensions
        return str(p).removesuffix(extensions)

    def filter_metadata(img_group, metadata):
        id_group = [i['id'] for i in img_group]
        return {
            **metadata,
            'images': {k: v for k, v in dict(metadata['images']).items() if v['id'] in id_group},
            'annotations': [a for a in metadata['annotations'] if a['image_id'] in id_group]
        }

    annotation_file_name = "_annotations.zumo.json"

    unzipped_output_path = remove_n_extensions(path_to_zipped_dataset, n=1)
    with zipfile.ZipFile(path_to_zipped_dataset, "r") as zip_ref:
        zip_ref.extractall(unzipped_output_path)

    for batch in listdir(unzipped_output_path):
        batch_uri = join(unzipped_output_path, batch)
        annotation_file_uri = join(batch_uri, annotation_file_name)
        metadata = json.load(open(annotation_file_uri))
        batch_images = list(dict(metadata['images']).values())
        # https://www.geeksforgeeks.org/python-identical-consecutive-grouping-in-list/
        grouped_images = [list(y) for x, y in groupby(
            batch_images,
            lambda x: remove_n_extensions(Path(x['relative_path']), n=2)
        )]

        for img_group in grouped_images:
            filtered_metadata = filter_metadata(img_group, metadata)
            uri_group = [
                join(batch_uri, Path(i['relative_path']))
                for i in img_group
            ]
            saver_func(uri_group, filtered_metadata)


def test_generate():
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig("can_v7")
    dataset = zpy.generate(dataset_config, num_datapoints=22,
                           materialize=True, saver_func=default_saver_func)
    print("Printing returned dataset:")
    print(json.dumps(dataset, default=lambda o: o.__dict__, sort_keys=True, indent=4))


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
    input_path = "/mnt/c/Users/georg/Zumo/Datasets/can_v714-8c288ec8.zip"
    format_dataset(input_path, default_saver_func)
    # test_generate()
