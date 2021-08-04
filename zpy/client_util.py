import functools
import hashlib
import json
import math
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
from pydash import values, filter_
from requests import HTTPError


def track_runtime(wrapped_function):
    @functools.wraps(wrapped_function)
    def do_track(*args, **kwargs):
        start_datetime = datetime.now()
        value = wrapped_function(*args, **kwargs)
        end_datetime = datetime.now()
        run_time = end_datetime - start_datetime
        print(
            f"{str(wrapped_function)} took {run_time.seconds}.{run_time.microseconds} seconds."
        )

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


def extract_zip(path_to_zip: Union[str, Path], output_path: Union[str, Path]):
    """
    Extracts a .zip at `path_to_zip` to a directory at `output_path`.

    Args:
        path_to_zip (Union[str, Path]): Location of .zip to extract.
        output_path (Union[str, Path]): Location of where to extract to.
    Returns:
        None: No return value
    """
    with zipfile.ZipFile(path_to_zip, "r") as zip_ref:
        zip_ref.extractall(output_path)


def write_json(path, json_blob):
    """
    Args:
        path (Path or str): Path to output to.
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


def group_metadata_by_datapoint(
    dataset_path: Path,
) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Updates metadata with new ids and accurate image paths.
    Returns a list of dicts, each item containing metadata relevant to a single datapoint.
    Args:
        dataset_path (Path): Path to unzipped dataset.
    Returns:
        tuple (metadata: dict, categories: list[dict], datapoints: list[dict]): Returns a tuple of (metadata,
            categories, datapoints), datapoints being a list of dicts, each containing a list of images and a list of
            annotations.
    """
    accum_metadata = {}
    accum_categories = {}
    accum_datapoints = []
    category_count_sums = defaultdict(int)

    # batch level - group images by satapoint
    for batch in listdir(dataset_path):
        batch_uri = join(dataset_path, batch)
        annotation_file_uri = join(batch_uri, "_annotations.zumo.json")

        with open(annotation_file_uri) as annotation_file:
            metadata = json.load(annotation_file)

        accum_metadata = {**metadata["metadata"], "save_path": batch_uri}

        for category_id, category in metadata["categories"].items():
            category_count_sums[category_id] += category["count"]

        for category_id, category in metadata["categories"].items():
            accum_categories[category_id] = category

        images_grouped_by_datapoint = group_by(
            values(metadata["images"]), lambda image: image["frame"]
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
                img["id"]: datapoint_uuid + "".join(Path(img["name"]).suffixes[-2:])
                for img in images
            }

            images_mutated = [
                {
                    **i,
                    "id": image_new_id_map[i["id"]],
                    "output_path": join(batch_uri, Path(i["relative_path"])),
                    "datapoint_id": datapoint_uuid,
                }
                for i in images
            ]

            annotations_mutated = [
                {
                    **a,
                    "id": str(uuid.uuid4()),
                    "image_id": image_new_id_map[a["image_id"]],
                    "datapoint_id": datapoint_uuid,
                }
                for a in annotations
            ]

            # accumulate
            accum_datapoints.append(
                {
                    "images": images_mutated,
                    "annotations": annotations_mutated,
                }
            )

    for category_id, category_count in category_count_sums.items():
        accum_categories[category_id]["count"] = category_count

    return accum_metadata, values(accum_categories), accum_datapoints
