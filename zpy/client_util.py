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
from pathlib import Path
from typing import Iterable, List, Dict, Tuple, Callable
from typing import Union

import requests
from pydash import values
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


def get_image_type_from_name(image_name):
    """
    Extracts the image type from the name.

    Args:
        image_name (str): Name of the image in the format `image.000000.rgb.png`
    Returns:
        str: The type of the image. Ex: `"image.000000.rgb.png"` -> `"rgb"`, `"image.000123.iseg.jpg"` -> `"iseg"`
    """
    return image_name.split(".")[-2]


def get_global_id(datapoint_uuid: str, local_id: int):
    """
    Creates a globally unique id by combining a locally unique id with its globally unique datapoint uuid.

    Args:
        datapoint_uuid (str): Id of the datapoint.
        local_id (int): Id of the local object (ex. image or annotation)
    Returns:
        str: The globally unique id of the local object.
    """
    return f"{datapoint_uuid[:8]}.{local_id}"


def group_metadata_by_datapoint(dataset_path: Path) -> Tuple[List[Dict], Dict]:
    """
    Aggregates and reformats the zumo metadata across all batches of a dataset.

    Args:
        dataset_path (Path): Path to unzipped dataset.
    Returns:
        tuple (datapoints: list[dict], categories: dict): Returns a tuple of (datapoints, categories).
    """
    categories = {}
    datapoints = []
    category_count_sums = defaultdict(int)

    # batch level - group images by datapoint
    for batch in dataset_path.iterdir():
        # Read batch specific zumo json file
        batch_uri = dataset_path / batch
        annotation_file_uri = batch_uri / "_annotations.zumo.json"
        with open(annotation_file_uri) as annotation_file:
            metadata = json.load(annotation_file)

        # Add the category counts to the category count accumulator
        for category_id, category in metadata["categories"].items():
            category_count_sums[int(category_id)] += category["count"]

        # Add the categories to the category accumulator
        # NOTE: This assumes categories are unique across batches which might not always be true.
        for category_id, category in metadata["categories"].items():
            categories[int(category_id)] = category

        # Group images by frame (ie. datapoint). Results in a list of lists.
        images_grouped_by_datapoint = group_by(
            values(metadata["images"]), lambda i: i["frame"]
        )

        # Reformat each datapoint
        for images in images_grouped_by_datapoint:
            # Unique identifier for this datapoint (will change per run)
            datapoint_uuid = str(uuid.uuid4())

            # Store as a map to make lookup a breeze. Ex. datapoint['images']['rgb'].
            image_type_to_image = {}
            for image in images:
                updated_image = {
                    # Take all previous image keys
                    **image,
                    # Update id to be globally unique across batches
                    "id": get_global_id(datapoint_uuid, image["id"]),
                    # Update the output_path (absolute path) to match where it exists on the local filesystem.
                    "output_path": batch_uri / image["relative_path"],
                }
                # Remove extra stuff to prevent propagating around with no clear use
                for key in ["name", "relative_path", "frame"]:
                    if key in updated_image:
                        del updated_image[key]

                image_type_to_image[
                    get_image_type_from_name(image["name"])
                ] = updated_image

            # Get datapoint specific annotations
            image_ids = [i["id"] for i in images]

            # Accumulate annotations. They're originally referenced via image id, but we're removing that lookup and
            # just saying that all the annotations in the list belong to one datapoint.
            annotations = []
            for annotation in metadata["annotations"]:
                if annotation["image_id"] in image_ids:
                    updated_annotation = {
                        # Take all annotation keys
                        **annotation,
                        # Update image id reference to the one which is globally unique across batches
                        "image_id": get_global_id(datapoint_uuid, annotation["id"]),
                    }
                    # Remove extra stuff to prevent propagating around with no clear use
                    for key in ["id", "frame"]:
                        if key in updated_annotation:
                            del updated_annotation[key]

                    annotations.append(updated_annotation)

            datapoint = {
                "id": datapoint_uuid,
                "images": image_type_to_image,
                "annotations": annotations,
            }
            datapoints.append(datapoint)

    # Override the category counts now that they've been accumulated across all batches
    for category_id, category_count in category_count_sums.items():
        categories[int(category_id)]["count"] = category_count

    return datapoints, categories
