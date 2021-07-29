import functools
import hashlib
import json
import math
import os
import shutil
import sys
import uuid
import zipfile
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from os import listdir
from os.path import join
from pathlib import Path
from typing import Iterable, List, Dict, Tuple, Callable
from typing import Union

import requests
from pydash import uniq, values, filter_
from requests import HTTPError


def track_runtime(wrapped_function):
    @functools.wraps(wrapped_function)
    def do_track(*args, **kwargs):
        start_datetime = datetime.now()
        value = wrapped_function(*args, **kwargs)
        end_datetime = datetime.now()
        run_time = end_datetime - start_datetime
        print(f"{str(wrapped_function)} took {run_time.seconds}.{run_time.microseconds} seconds.")

        return value

    return do_track


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


def remove_n_extensions(path: Union[str, Path], n: int) -> str:
    """
    Removes n extensions from the end of a path. Example: "image.rgb.png" becomes "image" for n = 2
    Args:
        path (Path): Path to manipulate.
        n (int): Number of extensions to remove.
    Returns:
        str: Path minus n extensions.
    """
    """"""
    p = Path(path)
    for _ in range(n):
        p = p.with_suffix("")
    return str(p)


def dict_hash(data) -> str:
    """
    Returns a deterministic hash from json serializable data.
    https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
    Args:
        data: JSON serializable data.
    Returns:
        str: Deterministic hash of the input data.
    """
    data_json = json.dumps(
        data,
        sort_keys=True,
    )
    dhash = hashlib.md5()
    encoded = data_json.encode()
    dhash.update(encoded)
    config_hash = dhash.hexdigest()
    return config_hash


@track_runtime
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


@track_runtime
def write_json(path, json_blob):
    """
    Args:
        path (str): Path to output to.
        json_blob (obj): JSON serializable object.
    """
    with open(path, "w") as outfile:
        json.dump(json_blob, outfile, indent=4)


def group_by(iterable: Iterable, keyfunc: Callable) -> List[List]:
    """
    Groups items in a list by equality using the value returned when passed to the callback
    https://docs.python.org/3/library/itertools.html#itertools.groupby
    Args:
        iterable (Iterable): List of items to group
        keyfunc (Callable): Callback that transforms each item in the list to a value used to test for equality against other items.
    Returns:
        list[list]: List of lists containing items that test equal to eachother when transformed by the keyfunc callback
    """
    return [
        list(group)
        for key, group in groupby(
            iterable,
            keyfunc,
        )
    ]


@track_runtime
def group_metadata_by_datapoint(
    dataset_path: Path,
) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Updates metadata with new ids and accurate image paths.
    Returns a list of dicts, each item containing metadata relevant to a single datapoint.
    Args:
        dataset_path (Path): Path to unzipped dataset.
    Returns:
        tuple (metadata: dict, categories: list[dict], datapoints: list[dict]): Returns a tuple of (metadata, categories, datapoints), datapoints being a list of dicts, each containing images and annotations.
    """
    print('Parsing dataset to group by datapoint...')
    accum_metadata = {}
    accum_categories = []
    accum_datapoints = []
    category_count_sums = defaultdict(int)

    # batch level - group images by satapoint
    for batch in listdir(dataset_path):
        batch_uri = join(dataset_path, batch)
        annotation_file_uri = join(batch_uri, "_annotations.zumo.json")

        with open(annotation_file_uri) as annotation_file:
            metadata = json.load(annotation_file)

        for c in values(metadata["categories"]):
            category_count_sums[c["id"]] += c["count"]

        images_grouped_by_datapoint = group_by(
            values(metadata["images"]),
            lambda image: remove_n_extensions(image["relative_path"], n=2),
        )

        # datapoint level
        for images in images_grouped_by_datapoint:
            datapoint_uuid = str(uuid.uuid4())

            # get datapoint specific annotations
            image_ids = [i["id"] for i in images]
            annotations = filter_(
                metadata["annotations"], lambda a: a["image_id"] in image_ids
            )

            # mutate
            image_new_id_map = {
                img["id"]: str(
                    datapoint_uuid
                    + "-"
                    + str(Path(img["name"]).suffixes[-2]).replace(".", "")
                )
                for img in images
            }

            categories_mutated = [
                {**c, "count": category_count_sums[c["id"]]}
                for c in values(metadata["categories"])
            ]

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

            # accumulate
            accum_metadata = {**metadata["metadata"], "save_path": batch_uri}
            accum_categories = uniq([*accum_categories, *categories_mutated])
            accum_datapoints.append(
                {
                    "images": images_mutated,
                    "annotations": annotations_mutated,
                }
            )

            # update the category counts
            accum_categories = [
                {**c, "count": category_count_sums[c["id"]]} for c in accum_categories
            ]

    return accum_metadata, accum_categories, accum_datapoints


def format_dataset(
    zipped_dataset_path: Union[str, Path], datapoint_callback=None
) -> None:
    """
    Updates metadata with new ids and accurate image paths.
    If a datapoint_callback is provided, it is called once per datapoint with the updated metadata.
    Otherwise the default is to write out an updated _annotations.zumo.json, along with all images, to a new adjacent folder.
    Args:
        zipped_dataset_path (str): Path to unzipped dataset.
        datapoint_callback (Callable) -> None: User defined function.
    Returns:
        None: No return value.
    """
    unzipped_dataset_path = Path(remove_n_extensions(zipped_dataset_path, n=1))
    if not unzipped_dataset_path.exists():
        print(f'Unzipping {zipped_dataset_path}...')
        unzipped_dataset_path = extract_zip(zipped_dataset_path)

    metadata, categories, datapoints = group_metadata_by_datapoint(
        unzipped_dataset_path
    )

    if datapoint_callback is not None:
        print('Skipping default formatting, using datapoint_callback instead.')
        for datapoint in datapoints:
            datapoint_callback(
                datapoint["images"], datapoint["annotations"], categories
            )

    else:
        print('Doing default formatting for dataset...')
        output_dir = join(unzipped_dataset_path.parent, unzipped_dataset_path.name, "_formatted")

        accum_metadata = {
            "metadata": {
                **metadata,
                "save_path": output_dir,
            },
            "categories": categories,
            "images": [],
            "annotations": [],
        }

        for datapoint in datapoints:
            accum_metadata["annotations"].extend(datapoint["annotations"])

            for image in datapoint["images"]:
                # reference original path to save from
                original_image_uri = image["output_path"]

                # build new path
                image_extensions = "".join(Path(image["name"]).suffixes[-2:])
                datapoint_uuid = "-".join(str(image["id"]).split("-")[:-1])
                new_image_name = datapoint_uuid + image_extensions
                output_image_uri = join(output_dir, Path(new_image_name))

                # add to accumulator
                accum_metadata["images"].append(
                    {
                        **image,
                        "name": new_image_name,
                        "output_path": output_image_uri,
                        "relative_path": new_image_name,
                    }
                )

                # copy image to new folder
                os.makedirs(os.path.dirname(output_image_uri), exist_ok=True)
                shutil.copy(original_image_uri, output_image_uri)

        # write json
        metadata_output_path = join(output_dir, Path("_annotations.zumo.json"))
        os.makedirs(os.path.dirname(metadata_output_path), exist_ok=True)
        with open(metadata_output_path, "w") as outfile:
            json.dump(accum_metadata, outfile, indent=4)
