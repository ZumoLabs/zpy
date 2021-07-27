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
import hashlib
from pydash import uniq


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
            query_param_values.append(f"{django_field_traversal}:{django_field_value}")
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


def dict_to_list(d: dict) -> list:
    """Converts dict to list"""
    return list(dict(d).values())


def remove_n_extensions(path: Union[str, Path], n: int) -> Path:
    """Takes a path and removes n extensions from the end. Example: "image.rgb.png" becomes "image" for n = 2"""
    p = Path(path)
    extensions = "".join(p.suffixes[-n:])  # remove n extensions
    return str(p).removesuffix(extensions)


def hash(data):
    """Return a deterministic hash of any json serializable data.
    https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
    """
    dict_json = json.dumps(
        data,
        sort_keys=True,
    )
    dhash = hashlib.md5()
    encoded = dict_json.encode()
    dhash.update(encoded)
    config_hash = dhash.hexdigest()
    return config_hash


def extract_zip(path_to_zip: Path) -> Path:
    """
    Extracts a .zip to a new adjacent folder by the same name.
    Args:
        path_to_zip: Path to .zip
    Returns:
        Path: Extracted folder path
    """
    unzipped_path = Path(remove_n_extensions(path_to_zip, n=1))
    with zipfile.ZipFile(path_to_zip, "r") as zip_ref:
        zip_ref.extractall(unzipped_path)
    return unzipped_path


def group_metadata_by_datapoint(dataset_path: Path) -> list[dict]:
    """
    Updates metadata with new ids and accurate image paths.
    Returns a list of dicts, each item containing metadata relevant to a single datapoint.
    Args:
        dataset_path (Path): Path to unzipped dataset.
    Returns:
        list[
            dict[
                metadata: list[dict],
                categories: list[dict],
                images: list[dict],
                annotations: list[dict],

            ]
        ]: Returns a list of dicts, each item containing metadata relevant to a single datapoint.
    """

    datapoint_list = []
    category_count_sums = {}

    # batch level - group images by satapoint
    for batch in listdir(dataset_path):
        batch_uri = join(dataset_path, batch)
        annotation_file_uri = join(batch_uri, "_annotations.zumo.json")
        metadata = json.load(open(annotation_file_uri))

        batch_categories = dict_to_list(metadata["categories"])
        for c in batch_categories:
            category_count_sums[c["id"]] = (
                category_count_sums.get(c["id"], 0) + c["count"]
            )

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
            category_ids = uniq([a["category_id"] for a in annotations])
            categories = [
                c
                for c in dict_to_list(metadata["categories"])
                if c["id"] in category_ids
            ]

            image_new_id_map = {
                img["id"]: str(
                    DATAPOINT_UUID
                    + "-"
                    + str(Path(img["name"]).suffixes[-2]).replace(".", "")
                )
                for img in images
            }

            # mutate the arrays
            images_mutated = [
                {
                    **i,
                    "output_path": join(batch_uri, Path(i["relative_path"])),
                    "id": image_new_id_map[i["id"]],
                }
                for i in images
            ]
            annotations_mutated = [
                {
                    **a,
                    "image_id": image_new_id_map[a["image_id"]],
                }
                for a in annotations
            ]
            categories_mutated = [
                {**c, "count": category_count_sums[c["id"]]} for c in categories
            ]
            metadata_mutated = {**metadata["metadata"], "save_path": batch_uri}

            datapoint_list.append(
                {
                    "metadata": metadata_mutated,
                    "categories": categories_mutated,
                    "images": images_mutated,
                    "annotations": annotations_mutated,
                }
            )

    def update_category_counts(datapoints):
        return [
            {
                **d,
                "categories": [
                    {**c, "count": category_count_sums[c["id"]]}
                    for c in d["categories"]
                ],
            }
            for d in datapoints
        ]

    return update_category_counts(datapoint_list)


def format_dataset(dataset_path: Union[str, Path], datapoint_callback=None) -> None:
    """
    Updates metadata with new ids and accurate image paths.
    If a datapoint_callback is provided, it is called once per datapoint with the updated metadata.
    Otherwise the default is to write out an updated _annotations.zumo.json, along with all images, to a new adjacent folder.
    Args:
        dataset_path (str): Path to unzipped dataset.
        datapoint_callback (images: list[dict], annotations: list[dict], categories: list[dict]) -> None: User defined function.
    Returns:
        None: No return value.
    """
    grouped_metadata = group_metadata_by_datapoint(dataset_path)

    if datapoint_callback is not None:
        for datapoint in grouped_metadata:
            datapoint_callback(
                datapoint["images"], datapoint["annotations"], datapoint["categories"]
            )
    else:
        output_dir = join(dataset_path.parent, dataset_path.name + "_formatted")

        accumulated_metadata = {
            "metadata": {},
            "categories": [],
            "images": [],
            "annotations": [],
        }

        for datapoint in grouped_metadata:
            accumulated_metadata["metadata"] = datapoint["metadata"]
            accumulated_metadata["categories"].extend(datapoint["categories"])
            accumulated_metadata["annotations"].extend(datapoint["annotations"])

            for image in datapoint["images"]:
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

        unique_metadata = {
            "metadata": {
                **accumulated_metadata["metadata"],
                "save_path": output_dir,
            },
            "categories": uniq(accumulated_metadata["categories"]),
            "images": uniq(accumulated_metadata["images"]),
            "annotations": uniq(accumulated_metadata["annotations"]),
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
