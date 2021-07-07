import functools
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from random import randrange
from typing import Dict, Union

import requests

from cli.utils import download_url
from client.util import (
    add_newline,
    get,
    post,
    to_query_param_value,
    convert_size,
    auth_header,
    clear_last_print,
    is_done,
)

_auth_token: str = ""
_base_url: str = ""
_project: Union[Dict, None] = None


def init(
    auth_token: str,
    project_uuid: str,
    base_url: str = "http://localhost:8000",
    **kwargs,
):
    global _auth_token, _base_url, _project
    _auth_token = auth_token
    _base_url = base_url

    try:
        _project = get(
            f"{_base_url}/api/v1/projects/{project_uuid}",
            headers=auth_header(_auth_token),
        )
    except requests.HTTPError:
        print(
            "Failed to find project, please double check the id and try again.",
            file=sys.stderr,
        )


IMAGES_PER_SAMPLE = 2  # for the iseg and rbg


def require_zpy_init(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if None in [_project, _auth_token, _base_url]:
            raise RuntimeError("zpy.init() must be called")
        return func(*args, **kwargs)

    return wrapper


class DatasetConfig:
    @require_zpy_init
    def __init__(self, sim_name: str, **kwargs):
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
        )["results"]
        if len(sims) > 1:
            raise RuntimeError(
                f"Create DatasetConfig failed: Found more than 1 Sim for unique filters which should not be possible."
            )
        elif len(sims) == 1:
            print(f"Found sim <{sim_name}> in project <{_project['name']}>")
            self._sim = sims[0]
        else:
            raise RuntimeError(
                f"Create DatasetConfig failed: Could not find Sim<{sim_name}> in Project<{_project['name']}>."
            )

    @property
    def sim(self):
        return self._sim

    @property
    def available_params(self):
        return self._sim["run_kwargs"]

    @property
    def config(self):
        """A mapping of flattened gin config fields to values.

        Ex:
        Given a desired json config that looks like this:
        {
            "fieldA": "a",
            "fieldB1": {
                "fieldB2": "b",
                "fieldC1: {
                    "fieldC2": "c"
                }
            }
        }

        _config should look like this:
        {
            "fieldA": "a",
            "fieldB1__fieldB2": "b",
            "fieldB1__fieldC1__fieldC2: "c"
        }
        """
        return self._config

    def set(self, parameter: str, value: any):
        """Set a value for a configurable parameter.

        Args:
            parameter: The flattened gin config path as described in _config.
            value: The value for the gin config path provided.
        """
        self._config[parameter] = value

    def remove(self, key):
        """Remove a configurable parameter.

        Args:
            Key should be the flattened gin config field as described in config.
        """
        self._config.pop(key, None)


@add_newline
def preview(dataset_config: DatasetConfig, num_samples=10):
    """
    Generate a preview of output data for a given DatasetConfig.

    Args:
        dataset_config: Describes a Sim and its configuration. See DatasetConfig.
        num_samples (int): number of preview samples to generate
    Returns:
        None
    """
    print(f"Generating preview:")

    config_filters = (
        {}
        if dataset_config is None
        else {"config": to_query_param_value(dataset_config.config)}
    )
    filter_params = {
        "project": _project["id"],
        "sim": dataset_config.sim["id"],
        "state": "READY",
        **config_filters,
    }
    data_sets = get(
        f"{_base_url}/api/v1/datasets/",
        params=filter_params,
        headers=auth_header(_auth_token),
    )["results"]

    if len(data_sets) == 0:
        print(f"No preview available.")
        print("\t(no premade data sets)")
        return

    # Choose random data set in page
    dataset_id = data_sets[randrange(len(data_sets))]["id"]
    # Re-request the data set detail (image links aren't included in the list call
    dataset = get(
        f"{_base_url}/api/v1/datasets/{dataset_id}/", headers=auth_header(_auth_token)
    )
    if len(dataset["files"]) == 0:
        print(f"No preview available.")
        print("\t(no images found)")
        return

    bounded_num_images = min([len(dataset["files"]), num_samples * IMAGES_PER_SAMPLE])
    formatted_samples = {}
    found_images = 0
    for sample in dataset["files"]:
        path = Path(sample["path"])
        name = path.name
        if (
            name.startswith("_plot")
            or name.startswith("_viz")
            or path.suffix in [".log", ".json"]
        ):
            continue

        image_category, name, output_type, file_ext = name.split(".")

        if name not in formatted_samples:
            formatted_samples[name] = {}

        formatted_samples[name][output_type] = sample
        found_images += 1

        if found_images == bounded_num_images:
            # Not pulling next page for now. Either find enough samples or we don't.
            break

    print(json.dumps(formatted_samples, indent=4, sort_keys=True))


@add_newline
def generate(
    name: str, dataset_config: DatasetConfig, num_datapoints: int, materialize=False
):
    """
    Generate a dataset.

    Args:
        name: Name of the dataset. Must be unique per Project.
        dataset_config: Specification for a Sim and its configurable parameters.
        num_datapoints: Number of datapoints in the dataset. A datapoint is an instant in time composed of all
                              the output images (rgb, iseg, cseg, etc) along with the annotations.
        materialize: Optionally download the dataset.
    Returns:
        None
    """
    dataset = post(
        f"{_base_url}/api/v1/datasets/",
        data={
            "project": _project["id"],
            "name": name,
        },
        headers=auth_header(_auth_token),
    )
    post(
        f"{_base_url}/api/v1/datasets/{dataset['id']}/generate",
        data={
            "project": _project["id"],
            "sim": dataset_config.sim["id"],
            "config": json.dumps(
                {
                    **dataset_config.config,
                    "amount": num_datapoints,
                }
            ),
        },
    )

    print("Generating dataset:")
    print(json.dumps(dataset, indent=4, sort_keys=True))
    print(
        f"You can follow its progress at app.zumolabs.ai/sims/{dataset_config.sim['id']}/sim-runs"
    )

    if materialize:
        dataset = get(f"{_base_url}/api/v1/datasets/{dataset['id']}")
        while "state" not in dataset or is_done(dataset["state"]):
            next_check_datetime = datetime.now() + timedelta(seconds=60)
            while datetime.now() < next_check_datetime:
                print(
                    f"Dataset is not ready. Checking again in {next_check_datetime - datetime.now()}s",
                    end="\r",
                )
                time.sleep(1)

            clear_last_print()
            print("Checking dataset...", end="\r")
            dataset = get(
                f"{_base_url}/api/v1/datasets/{dataset['id']}",
                headers=auth_header(_auth_token),
            ).json()

        if dataset["state"] == "READY":
            print("Dataset is ready for download.")
            dataset_download_res = get(
                f"{_base_url}/api/v1/datasets/{dataset['id']}/download",
                headers=auth_header(_auth_token),
            ).json()
            name_slug = f"{dataset['name'].replace(' ', '_')}-{dataset['id'][:8]}.zip"
            # Throw it in /tmp for now I guess
            output_path = Path("/tmp") / name_slug
            print(
                f"Downloading {convert_size(dataset_download_res['size_bytes'])} dataset to {output_path}..."
            )
            download_url(dataset_download_res["redirect_link"], output_path)
            print("Done.")
        else:
            print(
                f"Dataset is no longer running but cannot be downloaded with state = {dataset['state']}"
            )


class Dataset:
    _dataset = None

    @require_zpy_init
    def __init__(self, name: str):
        self._name = name

        unique_dataset_filters = {
            "project": _project["id"],
            "name": name,
        }
        datasets = get(
            f"{_base_url}/api/v1/datasets/",
            params=unique_dataset_filters,
            headers=auth_header(_auth_token),
        )["results"]
        self._dataset = datasets[0]

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        if not self._dataset:
            print("Dataset needs to be generated before you can access its state.")
        return self._dataset["state"]

    @property
    def config(self):
        return
