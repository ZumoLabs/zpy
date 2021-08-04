import functools
import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from typing import Union

import requests
from pydash import set_, unset, is_empty

from cli.utils import download_url
from zpy.client_util import (
    add_newline,
    get,
    post,
    to_query_param_value,
    convert_size,
    auth_header,
    clear_last_print,
    is_done,
    dict_hash,
    group_metadata_by_datapoint,
    extract_zip,
    write_json,
)

_auth_token: str = ""
_base_url: str = ""
_project: Union[Dict, None] = None


def init(
    auth_token: str,
    project_uuid: str,
    base_url: str = "https://ragnarok.zumok8s.org",
):
    """
    Initializes the zpy client library.

    Args:
        auth_token (str): API auth_token. Required for all internal API calls.
        project_uuid (str): A valid uuid4 project id. Required to scope permissions for all requested API objects.
        base_url (str, optional): API url. Overridable for testing different environments.
    Returns:
        None: No return value.
    """
    global _auth_token, _base_url, _project
    _auth_token = auth_token
    _base_url = base_url

    try:
        _project = get(
            f"{_base_url}/api/v1/projects/{project_uuid}",
            headers=auth_header(_auth_token),
        ).json()
    except requests.HTTPError:
        print(
            "Failed to find project, please double check the id and try again.",
            file=sys.stderr,
        )


DATASET_OUTPUT_PATH = Path("/tmp")  # for generate and default_saver_func


def require_zpy_init(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if None in [_project, _auth_token, _base_url]:
            raise RuntimeError("Project and auth_token must be set via zpy.init()")
        return func(*args, **kwargs)

    return wrapper


class DatasetConfig:
    @require_zpy_init
    def __init__(self, sim_name: str):
        """
        Create a DatasetConfig. Used by zpy.preview and zpy.generate.

        Args:
            sim_name: Name of Sim
        """
        self._sim = None
        self._config = {}

        unique_sim_filters = {
            "project": _project["id"],
            "name": sim_name,
        }
        sims = get(
            f"{_base_url}/api/v1/sims/",
            params=unique_sim_filters,
            headers=auth_header(_auth_token),
        ).json()["results"]
        if len(sims) > 1:
            raise RuntimeError(
                "Create DatasetConfig failed: Found more than 1 Sim for unique filters which should not be possible."
            )
        elif len(sims) == 1:
            print(f"Found Sim<{sim_name}> in Project<{_project['name']}>")
            self._sim = sims[0]
        else:
            raise RuntimeError(
                f"Create DatasetConfig failed: Could not find Sim<{sim_name}> in Project<{_project['name']}>."
            )

    @property
    def sim(self):
        """
        Returns:
            dict: The Sim object.
        """
        return self._sim

    @property
    def available_params(self):
        """
        Returns:
            dict[]: The Sim's adjustable parameters.
        """
        return self._sim["run_kwargs"]

    @property
    def config(self):
        """
        Property which holds the parameters managed via DatasetConfig.set() and DatasetConfig.unset()

        Returns:
            dict: A dict representing a json object of gin config parameters.
        """
        return self._config

    @property
    def hash(self):
        """
        Returns:
             str: A deterministic hash of the internal _config dictionary.
        """
        return dict_hash(self._config)[:8]

    def set(self, path: str, value: any):
        """
        Set a configurable parameter. Uses pydash.set_.

                https://pydash.readthedocs.io/en/latest/api.html#pydash.objects.set_

        Args:
            path: The json gin config path using pydash.set_ notation.
            value: The value to be set at the provided gin config path.
        Returns:
            None: No return value
        Examples:
            Given the following object, the value at path `a.b[0].c` is 1.

                    { a: { b: [ { c: 1 } ] } }
        """
        set_(self._config, path, value)

    def unset(self, path):
        """
        Remove a configurable parameter. Uses pydash.unset.

                https://pydash.readthedocs.io/en/latest/api.html#pydash.objects.unset

        Args:
            path: The json gin config path using pydash.set_ notation. Ex. given object { a: b: [{ c: 1 }]}, the value at path "a.b[0]c" is 1.
        Returns:
            None: No return value
        Examples:
            Given the following object, the value at path `a.b[0].c` is 1.

                    { a: { b: [ { c: 1 } ] } }
        """
        unset(self._config, path)


class Dataset:
    def __init__(self, name: str = None, dataset_config: DatasetConfig = None):
        """
        Construct a Dataset which is a local representation of a Dataset generated on the API.

        Args:
            name (str): The name of the Dataset.
            dataset_config (DatasetConfig): The [zpy.client.DatasetConfig][] used to generate this Dataset.
        """
        self._name = name
        self._config = dataset_config

    @property
    def name(self):
        """
        Returns:
            str: The Dataset's name.
        """
        return self._name

    @property
    def config(self):
        """
        Returns:
            DatasetConfig: The [zpy.client.DatasetConfig][] used to generate this Dataset.
        """
        return self._config


@add_newline
def preview(dataset_config: DatasetConfig, num_samples=10):
    """
    Generate a preview of output data for a given DatasetConfig.

    Args:
        dataset_config (DatasetConfig): Describes a Sim and its configuration. See DatasetConfig.
        num_samples (int): Number of preview samples to generate.
    Returns:
        dict[]: Sample images for the given configuration.
    """
    print("Generating preview:")

    config_filters = (
        {}
        if is_empty(dataset_config.config)
        else {"config": to_query_param_value(dataset_config.config)}
    )
    filter_params = {
        "project": _project["id"],
        "sim": dataset_config.sim["name"],
        "state": "READY",
        "page-size": num_samples,
        **config_filters,
    }
    simruns_res = get(
        f"{_base_url}/api/v1/simruns/",
        params=filter_params,
        headers=auth_header(_auth_token),
    )
    simruns = simruns_res.json()["results"]

    if len(simruns) == 0:
        print("No preview available.")
        print("\t(no SimRuns matching filter)")
        return []

    file_query_params = {
        "run__sim": dataset_config.sim["id"],
        "path__icontains": ".rgb",
        "~path__icontains": ".annotated",
    }
    files_res = get(
        f"{_base_url}/api/v1/files/",
        params=file_query_params,
        headers=auth_header(_auth_token),
    )
    files = files_res.json()["results"]
    if len(files) == 0:
        print("No preview available.")
        print("\t(no images found)")
        return []

    return files


def default_dataset_callback(
    datapoints: list, categories: list, output_dir: Path
):
    """
    The default Dataset formatting function. It will flatten the Dataset into a single directory of images with a
    single annotation json file.

    A Datapoint object is of the following shape:

            {
                # Globally unique identifier for the datapoint
                "id": uuid.uuid4(),

                # The images in the datapoint
                "images": list of Image,

                # The annotations in the datapoint
                "annotations": list of Annotation,
            }

    An Image object is of the following shape:

            {
                # Globally unique identifier for the image
                "id": uuid.uuid4(),

                # Absolute path to the image
                "output_path": "absolute/path/to/image-name.file-suffix",

                # Relative path to the image within its parent folder
                "relative_path": "image-name.file-suffix",

                # Name of the image without the file suffix
                "name": "image-name",

                # There may be other arbitrary keys as per the Sim creator's discretion
                ...
            }

    An Annotation object is of the following shape:

            {
                # Globally unique identifier for the annotation
                "id": uuid.uuid4(),

                # Id of the image which this annotation is describing.
                "image_id": uuid.uuid4(),

                # There may be other arbitrary keys as per the Sim creator's discretion
                ...
            }

    A Category object is of the following shape:

            {
                # Unique identifier of this category across the Dataset
                "id": int,

                # Human readable name of the category
                "name": str,

                # Global count of this category across the Dataset
                "count": int,

                # There may be other arbitrary keys as per the Sim creator's discretion. Some common examples:
                "supercategories": list of dict,
                "subcategories": list of dict,
                "subcategory_count": list of dict,
                "color": 3-tuple,  # RGB decimal values
            }

    Args:
        datapoints (list of dict): List of Datapoint objects.
        categories (list of dict): List of Category objects.
        output_dir (Path): Default output location.
    Returns:
        None: No return value.
    """
    print(f"Doing default formatting and outputting to {output_dir}")

    if Path(output_dir).exists():
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    accum_metadata = {
        "categories": {category["id"]: category for category in categories},
        "images": {},
        "annotations": [],
    }

    for datapoint in datapoints:
        accum_metadata["annotations"].extend(datapoint["annotations"])

        for image in datapoint["images"]:
            # reference original path to save from
            original_image_uri = image["output_path"]

            # build new path
            output_image_uri = output_dir / image["id"]

            # add to accumulator
            accum_metadata["images"][image["id"]] = {
                **image,
                "name": image["id"],
                "relative_path": image["id"],
                "output_path": str(output_dir / image["id"]),
            }

            # copy image to new folder
            shutil.copy(original_image_uri, output_image_uri)

    # write json
    metadata_output_path = output_dir / "_annotations.zumo.json"

    os.makedirs(os.path.dirname(metadata_output_path), exist_ok=True)
    write_json(metadata_output_path, accum_metadata)


@add_newline
def generate(
    dataset_config: DatasetConfig,
    num_datapoints: int = 10,
    download: bool = True,
    dataset_callback=default_dataset_callback,
):
    """
    Generate a dataset.
    Args:
        dataset_config (DatasetConfig): Specification for a Sim and its configurable parameters.
        num_datapoints (int): Number of datapoints in the Dataset. A datapoint is an instant in time composed of all
                              the output images (rgb, iseg, cseg, etc) along with the annotations.
        dataset_callback (fn): See [zpy.client.default_dataset_callback][]. Called with formatted objects representing
             the Dataset.
        download (bool): Optionally download the Dataset. Defaults to True.
    Returns:
        Dataset: The created [zpy.client.Dataset][].
    """
    dataset_config_hash = dataset_config.hash
    sim_name = dataset_config.sim["name"]
    internal_dataset_name = f"{sim_name}-{dataset_config_hash}-{num_datapoints}"

    filter_params = {"project": _project["id"], "name": internal_dataset_name}

    datasets_res = get(
        f"{_base_url}/api/v1/datasets",
        params=filter_params,
        headers=auth_header(_auth_token),
    ).json()

    if len(datasets_res["results"]) == 0:
        dataset = post(
            f"{_base_url}/api/v1/datasets/",
            data={
                "project": _project["id"],
                "name": internal_dataset_name,
            },
            headers=auth_header(_auth_token),
        ).json()
        post(
            f"{_base_url}/api/v1/datasets/{dataset['id']}/generate/",
            data={
                "project": _project["id"],
                "sim": dataset_config.sim["name"],
                "config": json.dumps(dataset_config.config),
                "amount": num_datapoints,
            },
            headers=auth_header(_auth_token),
        )
        print(f"Sending generate request for Dataset<{internal_dataset_name}>...")
        print(json.dumps(dataset, indent=4, sort_keys=True))
    else:
        print(
            f"Generate for Dataset<{internal_dataset_name}> has already been requested."
        )
        dataset = datasets_res["results"][0]

    if download:
        print(f"Downloading Dataset<{internal_dataset_name}>...")
        dataset = get(
            f"{_base_url}/api/v1/datasets/{dataset['id']}/",
            headers=auth_header(_auth_token),
        ).json()
        while not is_done(dataset["state"]):
            all_simruns_query_params = {"datasets": dataset["id"]}
            num_simruns = get(
                f"{_base_url}/api/v1/simruns/",
                params=all_simruns_query_params,
                headers=auth_header(_auth_token),
            ).json()["count"]
            num_ready_simruns = get(
                f"{_base_url}/api/v1/simruns/",
                params={**all_simruns_query_params, "state": "READY"},
                headers=auth_header(_auth_token),
            ).json()["count"]
            next_check_datetime = datetime.now() + timedelta(seconds=60)
            while datetime.now() < next_check_datetime:
                print(
                    f"Dataset<{dataset['name']}> not ready for download in state {dataset['state']}. "
                    f"SimRuns READY: {num_ready_simruns}/{num_simruns}. "
                    f"Checking again in {(next_check_datetime - datetime.now()).seconds}s.",
                    end="\r",
                )
                time.sleep(1)
            clear_last_print()
            print(f"Checking state of Dataset<{dataset['name']}>...", end="\r")
            dataset = get(
                f"{_base_url}/api/v1/datasets/{dataset['id']}/",
                headers=auth_header(_auth_token),
            ).json()

        if dataset["state"] == "READY":
            dataset_download_res = get(
                f"{_base_url}/api/v1/datasets/{dataset['id']}/download/",
                headers=auth_header(_auth_token),
            ).json()

            # Make local path variables
            dataset_zip_path = Path(DATASET_OUTPUT_PATH) / f"{dataset['name']}.zip"
            dataset_unzipped_path = Path(DATASET_OUTPUT_PATH) / f"{dataset['name']}_raw"
            if not dataset_zip_path.exists():
                # Download if the zip is not found locally
                print(
                    f"Dataset<{dataset['name']}> not found locally, downloading "
                    f"{convert_size(dataset_download_res['size_bytes'])}..."
                )
                download_url(dataset_download_res["redirect_link"], dataset_zip_path)

                # Remove the unzipped folder if it exists from a previous run
                if dataset_unzipped_path.exists():
                    shutil.rmtree(dataset_unzipped_path)

                # Unzip the local dataset
                extract_zip(dataset_zip_path, dataset_unzipped_path)
            else:
                print(f"Dataset<{dataset['name']}> already exists locally.")

            print(f"Formatting Dataset<{dataset['name']}>...")
            metadata, categories, datapoints = group_metadata_by_datapoint(
                dataset_unzipped_path
            )

            dataset_callback(
                datapoints, categories, output_dir=dataset_zip_path.with_suffix("")
            )
        else:
            print(
                f"Dataset<{dataset['name']}> is no longer running but cannot be downloaded with "
                f"state = {dataset['state']}"
            )

    print(f"Dataset<{dataset['name']}> finished processing.")
    return Dataset(internal_dataset_name, dataset_config)
