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
    zpy.generate("dumpster_v2.21", dataset_config,
                 num_datapoints=3, materialize=True)


def pretty_print(object):
    try:
        json.dumps(object)
    except TypeError:
        print("Unable to serialize the object")
    else:
        print(json.dumps(object, indent=4))


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
    UUID = str(uuid.uuid4())

    for uri in image_uris:
        image = next((i for i in images if i["name"] in uri), None)

        if image is not None:
            unzipped_dataset_path = Path(
                str(uri).removesuffix(str(image["relative_path"]))
            ).parent

            output_path = join(
                unzipped_dataset_path.parent, unzipped_dataset_path.name + "_formatted"
            )

            output_file_uri = join(
                output_path,
                UUID + "-" + image["name"],
            )

            try:
                shutil.copy(uri, output_file_uri)
            except IOError as io_err:
                os.makedirs(os.path.dirname(output_file_uri))
                shutil.copy(uri, output_file_uri)


def format_dataset(path_to_zipped_dataset, saver_func):
    def remove_n_extensions(path: Union[str, Path], n: int = 1) -> Path:
        p = Path(path)
        extensions = "".join(p.suffixes[-n:])  # remove n extensions
        return str(p).removesuffix(extensions)

    def filter_metadata(img_group, metadata):
        id_group = [i["id"] for i in img_group]
        return {
            **metadata,
            "images": {
                k: v for k, v in dict(metadata["images"]).items() if v["id"] in id_group
            },
            "annotations": [
                a for a in metadata["annotations"] if a["image_id"] in id_group
            ],
        }

    annotation_file_name = "_annotations.zumo.json"

    unzipped_output_path = remove_n_extensions(path_to_zipped_dataset, n=1)
    with zipfile.ZipFile(path_to_zipped_dataset, "r") as zip_ref:
        zip_ref.extractall(unzipped_output_path)

    for batch in listdir(unzipped_output_path):
        batch_uri = join(unzipped_output_path, batch)
        annotation_file_uri = join(batch_uri, annotation_file_name)
        metadata = json.load(open(annotation_file_uri))
        batch_images = list(dict(metadata["images"]).values())
        # https://www.geeksforgeeks.org/python-identical-consecutive-grouping-in-list/
        grouped_images = [
            list(y)
            for x, y in groupby(
                batch_images,
                lambda x: remove_n_extensions(Path(x["relative_path"]), n=2),
            )
        ]

        for img_group in grouped_images:
            filtered_metadata = filter_metadata(img_group, metadata)
            uri_group = [join(batch_uri, Path(i["relative_path"]))
                         for i in img_group]
            saver_func(uri_group, filtered_metadata)


def new_saver_func(image_uris, metadata):
    images = list(dict(metadata["images"]).values())
    UUID = str(uuid.uuid4())

    for uri in image_uris:
        image = next((i for i in images if i["name"] in uri), None)

        if image is not None:
            unzipped_dataset_path = Path(
                str(uri)
                .removesuffix(str(image['relative_path']))
            ).parent

            output_path = join(
                unzipped_dataset_path.parent,
                unzipped_dataset_path.name + "_formatted"
            )

            output_file_uri = join(
                output_path,
                UUID
                + "-"
                + image['name'],
            )

            try:
                shutil.copy(uri, output_file_uri)
            except IOError as io_err:
                os.makedirs(os.path.dirname(output_file_uri))
                shutil.copy(uri, output_file_uri)


def remove_n_extensions(path: Union[str, Path], n: int = 1) -> Path:
    p = Path(path)
    extensions = "".join(p.suffixes[-n:])  # remove n extensions
    return str(p).removesuffix(extensions)


def unzip_to_path(path_to_zip: Union[str, Path], output_path: Union[str, Path]):
    with zipfile.ZipFile(path_to_zip, "r") as zip_ref:
        zip_ref.extractall(output_path)


def process_datapoint(unzipped_dataset_path, datapoint_callback):
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
            annotations = [a for a in metadata["annotations"]
                           if a["image_id"] in image_ids]
            category_ids = list(set([a["category_id"] for a in annotations]))
            categories = [c for c in list(
                dict(metadata["categories"]).values()) if c["id"] in category_ids]

            # functions that take ids and return new ones
            def mutate_category_id(category_id: Union[str, int]) -> str:
                return {str(c["id"]): (str(c["id"]) + "-" + BATCH_UUID)
                        for c in categories}[str(category_id)]

            def mutate_image_id(image_id: Union[str, int]) -> str:
                return {str(img['id']): str(DATAPOINT_UUID + "-" + str(Path(img['name']).suffixes[-2]).replace(".", ""))
                        for img in images}[str(image_id)]

            # mutate the arrays
            images_mutated = [
                {**i,
                 "output_path": join(batch_uri, Path(i["relative_path"])),
                 "id": mutate_image_id(i['id']),
                 } for i in images
            ]
            annotations_mutated = [
                {**a,
                 "category_id": mutate_category_id(a["category_id"]),
                 "image_id": mutate_image_id(a['image_id'])
                 } for a in annotations
            ]
            categories_mutated = [
                {**c,
                 "id":  mutate_category_id(c["id"])
                 } for c in categories
            ]

            # call the callback with the mutated arrays
            datapoint_callback(
                images_mutated, annotations_mutated, categories_mutated)


def process_zipped_dataset(path_to_zipped_dataset, datapoint_callback=None):

    def remove_n_extensions(path: Union[str, Path], n: int = 1) -> Path:
        p = Path(path)
        extensions = "".join(p.suffixes[-n:])  # remove n extensions
        return str(p).removesuffix(extensions)

    def unzip_to_path(path_to_zip: Union[str, Path], output_path: Union[str, Path]):
        with zipfile.ZipFile(path_to_zip, "r") as zip_ref:
            zip_ref.extractall(output_path)

    def call_per_datapoint(unzipped_dataset_path, datapoint_callback):
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
                    lambda x: remove_n_extensions(
                        Path(x["relative_path"]), n=2),
                )
            ]

            # datapoint level
            for images in images_grouped_by_datapoint:
                DATAPOINT_UUID = str(uuid.uuid4())
                # get [images], [annotations], [categories] per data point
                image_ids = [i["id"] for i in images]
                annotations = [a for a in metadata["annotations"]
                               if a["image_id"] in image_ids]
                category_ids = list(set([a["category_id"]
                                    for a in annotations]))
                categories = [c for c in list(
                    dict(metadata["categories"]).values()) if c["id"] in category_ids]

                # functions that take ids and return new ones
                def mutate_category_id(category_id: Union[str, int]) -> str:
                    return {str(c["id"]): (str(c["id"]) + "-" + BATCH_UUID)
                            for c in categories}[str(category_id)]

                def mutate_image_id(image_id: Union[str, int]) -> str:
                    return {str(img['id']): str(DATAPOINT_UUID + "-" + str(Path(img['name']).suffixes[-2]).replace(".", ""))
                            for img in images}[str(image_id)]

                # mutate the arrays
                images_mutated = [
                    {**i,
                     "output_path": join(batch_uri, Path(i["relative_path"])),
                     "id": mutate_image_id(i['id']),
                     } for i in images
                ]
                annotations_mutated = [
                    {**a,
                     "category_id": mutate_category_id(a["category_id"]),
                     "image_id": mutate_image_id(a['image_id'])
                     } for a in annotations
                ]
                categories_mutated = [
                    {**c,
                     "id":  mutate_category_id(c["id"])
                     } for c in categories
                ]

                # call the callback with the mutated arrays
                datapoint_callback(
                    images_mutated, annotations_mutated, categories_mutated)

    unzipped_dataset_path = Path(
        remove_n_extensions(path_to_zipped_dataset, n=1))
    unzip_to_path(path_to_zipped_dataset, unzipped_dataset_path)
    output_dir = join(
        unzipped_dataset_path.parent,
        unzipped_dataset_path.name + "_formatted"
    )

    # if no callback provided, use default accumulator and write to json file
    if (datapoint_callback is None):
        accumulated_metadata = {
            "images": [],
            "annotations": [],
            "categories": []
        }

        def default_datapoint_callback(images, annotations, categories):
            # accumulate json
            accumulated_metadata["annotations"].extend(annotations)
            accumulated_metadata["categories"].extend(categories)

            for image in images:
                # reference original path to save from
                original_image_uri = image["output_path"] 
                
                # build new path
                image_extensions = "".join(Path(image['name']).suffixes[-2:])
                datapoint_uuid = "-".join(str(image['id']).split("-")[:-1])
                new_image_name = datapoint_uuid + image_extensions
                output_image_uri = join(
                    output_dir,
                    Path(new_image_name)
                )

                # add to accumulator
                image = {
                    **image,
                    "name": new_image_name,
                    "output_path": output_image_uri,
                    "relative_path": new_image_name
                }
                accumulated_metadata["images"].append(image)

                # save image to new folder
                try:
                    shutil.copy(original_image_uri, output_image_uri)
                except IOError as io_err:
                    os.makedirs(os.path.dirname(output_image_uri))
                    shutil.copy(original_image_uri, output_image_uri)

        call_per_datapoint(unzipped_dataset_path, default_datapoint_callback)

        # https://www.geeksforgeeks.org/python-removing-duplicate-dicts-in-list/
        unique_elements_metadata = {k: [i for n, i in enumerate(v) if i not in v[n + 1:]]
                                    for k, v in accumulated_metadata.items()}
        # write json
        metadata_output_path = join(output_dir, Path("_annotations.zumo.json"))
        try:
            with open(metadata_output_path, 'w') as outfile:
                json.dump(unique_elements_metadata, outfile)
        except IOError as io_err:
            os.makedirs(os.path.dirname(metadata_output_path))
            with open(metadata_output_path, 'w') as outfile:
                json.dump(unique_elements_metadata, outfile)

    # else call the provided callback
    else:
        call_per_datapoint(unzipped_dataset_path, datapoint_callback)


# def unzip_and_flatten_dataset(datapoints, dataset):
#     annotation_accumulator = {}
#     dataset_name = dataset['name']
#     for datapoint in datapoints:
#         datapoint_uuid = uuid4()
#         for image in datapoint['images']:
#             type = Path(image['path'])[-2]  # Just guessed, Keaton figured this out already
#             image_id = f"{datatpoint_uuid}.{type}"
#             new_path = f"{DEFAULT_LOCATION}/{dataset_name}/{image_id}.png
#             copy(image['path'], new_path)
#             image['path'] = new_path
#             image['id'] = image_id
#         for annotation in datapoint['annotations']:
#             # just add annotation to reference the rgb image? this is how can_v7 looks i believe
#             annotation['image_id'] = f'{datapoint_uuid}.rgb'
#             annotation_accumulator['annotations'].append(annotation)
#             annotation_accumulator['images'].append(images)
#         for category in datapoint['categories']:
#             if category['id'] not in annotation_accumulator['categories']:
#                 annotation_accumulator['categories'][category['id']] = category
#     write_to_file(json.dumps(annotation_accumulator, indent=4))
# # calling code
# datapoints = prepare_dataset(dataset)
# if saver_func is None:
#     flatten_dataset(datapoints, dataset)
# else:
#     for datapoint in datapoints:
#         saver_func(datapoint['images'], datapoint['annotations'], datapoint['categories'])


def test_generate():
    zpy.init(**init_kwargs)
    dataset_config = zpy.DatasetConfig("trailer")
    dataset = zpy.generate(
        dataset_config,
        num_datapoints=3,
        # materialize=True,
        saver_func=default_saver_func,
    )
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
    process_zipped_dataset(input_path)
    # test_generate()
