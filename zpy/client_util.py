import functools
import math
import sys
from typing import Union
import requests
from requests import HTTPError
from typing import Union
import functools
import json
import sys
from pathlib import Path
from os import listdir
from os.path import join
import os
import shutil
import zipfile
from pathlib import Path
from itertools import groupby
import uuid


def add_newline(func):
    """Decorator to print a new line after the function call.

    Args:
        func: function to wrap

    Returns:
        wrapped function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        print("\n")
        return ret

    return wrapper


def auth_header(auth_token):
    return {"Authorization": f"Token {auth_token}"}


def handle_response(response: requests.Response):
    """Shared logic for handling API responses.

    Args:
        response: Request to handle
    Returns:
        requests.Response
    """
    if response.status_code != 200:
        if response.status_code == 400:
            # Known error from the server will have a nice message.
            raise HTTPError(response.json())
        else:
            response.raise_for_status()

    return response


def get(url, **kwargs):
    """GET a url. Forwards kwargs to requests.get
    TODO: Merge with calling code in zpy/cli/

    Args:
        url (str): Ragnarok API url
        kwargs: Forwarded to the requests.get function call
    Returns:
        requests.Response
    Raises:
        HTTPError
    """
    verbose = kwargs.pop("verbose", False)
    response = requests.get(url, **kwargs)
    if verbose:
        print(response.url)
    return handle_response(response)


def post(url, **kwargs):
    """POST to a url. Forwards kwargs to requests.post
    TODO: Merge with calling code in zpy/cli/

    Args:
        url (str): Ragnarok API url
        kwargs: Forwarded to the requests.post function call
    Returns:
         requests.Response
    Raises:
        HTTPError
    """
    return handle_response(requests.post(url, **kwargs))


def to_query_param_value(config):
    """Create the special query parameter value string for filtering generated-data-sets via config values.

    Args:
        config (dict): A dict of gin config values pre-flattened by using django field traversal notation. See Dataset._config
    Returns:
        string value for the config url query parameter
    """
    query_param_values = []
    for django_field_traversal, django_field_value in config.items():
        # Ignore fields set as None. They weren't specifically set or asked for.
        if django_field_value is not None:
            query_param_values.append(
                f"{django_field_traversal}:{django_field_value}")
    return ",".join(query_param_values)


def remove_none_values(obj: dict):
    """Recreates a dictionary from obj by omitting all key/value pairs where value is None."""
    return {k: v for k, v in obj.items() if v is not None}


def convert_size(size_bytes: int):
    """Converts a number of bytes into a pretty string."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


ERASE_LINE = "\x1b[2K"


def clear_last_print():
    sys.stdout.write(ERASE_LINE)


def is_done(state: str):
    """Returns True if state is a done state, false otherwise."""
    return state in ["READY", "CANCELLED", "PACKAGING_FAILED", "GENERATING_FAILED"]


def unique_list(list: list) -> list:
    """Removes non unique items from a list. Works for objects, unlike set()"""
    return [i for n, i in enumerate(list) if i not in list[n + 1:]]


def list_from_dict(d: dict):
    """Converts dict to list"""
    return list(dict(d).values())


def remove_n_extensions(path: Union[str, Path], n: int) -> Path:
    """Takes a path and removes n extensions from the end. Example: "image.rgb.png" becomes "image" for n = 2"""
    p = Path(path)
    extensions = "".join(p.suffixes[-n:])  # remove n extensions
    return str(p).removesuffix(extensions)


def unzip_to_path(path_to_zip: Union[str, Path], output_path: Union[str, Path]):
    """Extracts .zip at path to output_path."""
    with zipfile.ZipFile(path_to_zip, "r") as zip_ref:
        zip_ref.extractall(output_path)


def extract_zip(path_to_zip: Path) -> Path:
    """
    Extracts a .zip to a new adjacent folder by the same name.
    Args:
        path_to_zip: Path to .zip
    Returns:
        Path: Extracted folder path
    """
    unzipped_path = Path(
        remove_n_extensions(path_to_zip, n=1))
    with zipfile.ZipFile(path_to_zip, "r") as zip_ref:
        zip_ref.extractall(unzipped_path)
    return unzipped_path


def process_and_call_datapoints(dataset_path, datapoint_callback=None, default_datapoint_callback=None):
    """
    Updates metadata with new 
    Calls datapoint_callback or default_datapoint_callback once per datapoint.
    Args:
        dataset_path (Path): Path to raw, unzipped dataset.
        datapoint_callback (images: list(dict), annotations: list(dict), categories: list(dict)) -> any: User defined function.
        default_datapoint_callback (images: list(dict), annotations: list(dict), categories: list(dict), metadata: dict) -> any: Default function that accumaltes json and saves images..
    Returns:
        Path: Extracted folder path
    """
    # batch level - sum category counts
    category_count_sums = {}
    for batch in listdir(dataset_path):
        batch_uri = join(dataset_path, batch)
        annotation_file_uri = join(batch_uri, "_annotations.zumo.json")
        metadata = json.load(open(annotation_file_uri))
        batch_categories = list_from_dict(metadata["categories"])
        for c in batch_categories:
            category_count_sums[c["id"]] = category_count_sums.get(
                c["id"], 0) + c["count"]

    # batch level - group images by satapoint
    for batch in listdir(dataset_path):
        batch_uri = join(dataset_path, batch)
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
            annotations = [
                a for a in metadata["annotations"] if a["image_id"] in image_ids
            ]
            category_ids = unique_list([a["category_id"]
                                        for a in annotations])
            categories = [
                c
                for c in list_from_dict(metadata["categories"])
                if c["id"] in category_ids
            ]

            def mutate_image_id(image_id: Union[str, int]) -> str:
                id_map = {
                    str(img["id"]): str(
                        DATAPOINT_UUID
                        + "-"
                        + str(Path(img["name"]).suffixes[-2]
                              ).replace(".", "")
                    )
                    for img in images
                }
                return id_map[str(image_id)]

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
                    "image_id": mutate_image_id(a["image_id"]),
                }
                for a in annotations
            ]
            categories_mutated = [
                {**c,
                    "count": category_count_sums[c["id"]]
                 } for c in categories
            ]
            metadata_mutated = {
                **metadata["metadata"],
                "save_path": batch_uri
            }

            # call the callback with the mutated arrays - default callback includes metadata
            if (default_datapoint_callback is not None):
                default_datapoint_callback(
                    images_mutated, annotations_mutated, categories_mutated, metadata_mutated
                )
            elif (datapoint_callback is not None):
                datapoint_callback(
                    images_mutated, annotations_mutated, categories_mutated,
                )


def format_dataset(dataset_path: Union[str, Path], datapoint_callback=None):
    """
    Updates dataset metadata with new ids and accurate image paths.
    If a datapoint_callback is provided, it is called once per datapoint with the updated metadata.
    Otherwise it defaults to writing an updated _annotations.zumo.json, along with all images, to a new adjacent folder.
    Args:
        dataset_path (str): Path to raw unzipped dataset.
        datapoint_callback (images: list(dict), annotations: list(dict), categories: list(dict)) -> any: User defined function.
    Returns:
        None: No return value.
    """
    if (datapoint_callback is not None):
        process_and_call_datapoints(
            dataset_path, datapoint_callback=datapoint_callback)
    else:
        output_dir = join(
            dataset_path.parent, dataset_path.name + "_formatted"
        )

        accumulated_metadata = {
            "metadata": [],
            "images": [],
            "annotations": [],
            "categories": []
        }

        def default_datapoint_callback(images, annotations, categories, metadata):
            # accumulate json
            accumulated_metadata["metadata"].append(metadata)
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

        process_and_call_datapoints(dataset_path,
                                    default_datapoint_callback=default_datapoint_callback)

        # https://www.geeksforgeeks.org/python-removing-duplicate-dicts-in-list/
        unique_metadata = {
            k: (unique_list(v) if (isinstance(v, list)) else v) for k, v in accumulated_metadata.items()
        }

        # set "metadata" as the first one and update its output path
        unique_metadata["metadata"] = {
            **unique_metadata["metadata"][0],
            "save_path": output_dir
        }

        # write json
        metadata_output_path = join(output_dir, Path("_annotations.zumo.json"))
        try:
            with open(metadata_output_path, "w") as outfile:
                json.dump(unique_metadata, outfile)
        except IOError as io_err:
            os.makedirs(os.path.dirname(metadata_output_path))
            with open(metadata_output_path, "w") as outfile:
                json.dump(unique_metadata, outfile)
