import functools
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Union
import re

import hashlib
from os import listdir
from os.path import join
import os
import shutil
import zipfile
from pathlib import Path
from typing import Union
from itertools import groupby
import uuid

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
)

_auth_token: str = ""
_base_url: str = ""
_project: Union[Dict, None] = None


def init(
    auth_token: str,
    project_uuid: str,
    base_url: str = "https://ragnarok.zumok8s.org",
    **kwargs,
):
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


IMAGES_PER_SAMPLE = 2  # for the iseg and rbg
DATASET_OUTPUT_PATH = Path("/tmp")  # for generate and default_saver_func


def process_zipped_dataset(path_to_zipped_dataset, datapoint_callback=None):
    def remove_n_extensions(path: Union[str, Path], n: int = 1) -> Path:
        p = Path(path)
        extensions = "".join(p.suffixes[-n:])  # remove n extensions
        return str(p).removesuffix(extensions)

    def unzip_to_path(path_to_zip: Union[str, Path], output_path: Union[str, Path]):
        with zipfile.ZipFile(path_to_zip, "r") as zip_ref:
            zip_ref.extractall(output_path)

    unzipped_dataset_path = Path(
        remove_n_extensions(path_to_zipped_dataset, n=1))
    unzip_to_path(path_to_zipped_dataset, unzipped_dataset_path)
    output_dir = join(
        unzipped_dataset_path.parent,
        unzipped_dataset_path.name + "_formatted"
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
    if (datapoint_callback is not None):
        preprocess_datapoints(unzipped_dataset_path, datapoint_callback)

    # if no callback provided -  use default json accumulator, write out json, rename and copy images to new folder
    else:
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

        preprocess_datapoints(unzipped_dataset_path,
                              default_datapoint_callback)

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




def require_zpy_init(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if None in [_project, _auth_token, _base_url]:
            raise RuntimeError("Project and auth_token must be set via zpy.init()")
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
        return self._sim

    @property
    def available_params(self):
        return self._sim["run_kwargs"]

    @property
    def config(self):
        """A dict representing a json object of gin config parameters."""
        return self._config

    @property
    def hash(self):
        """Return a hash of the config.
        https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
        """
        config_json = json.dumps(
            self._config,
            sort_keys=True,
        )
        dhash = hashlib.md5()
        encoded = config_json.encode()
        dhash.update(encoded)
        config_hash = dhash.hexdigest()
        return config_hash

    def set(self, path: str, value: any):
        """Set a value for a configurable parameter.

        Args:
            path: The json gin config path. Ex. given object { a: b: [{ c: 1 }]}, the value at path "a.b[0]c" is 1.
            value: The value for the gin config path provided.
        """
        set_(self._config, path, value)

    def unset(self, path):
        """Remove a configurable parameter.

        Args:
            See self.set
        """
        unset(self._config, path)


@add_newline
def preview(dataset_config: DatasetConfig, num_samples=10):
    """
    Generate a preview of output data for a given DatasetConfig.

    Args:
        dataset_config: Describes a Sim and its configuration. See DatasetConfig.
        num_samples (int): number of preview samples to generate
    Returns:
        File[]: Sample images for the given configuration.
    """
    print("Generating preview:")

    config_filters = (
        {}
        if is_empty(dataset_config.config)
        else {"config": to_query_param_value(dataset_config.config)}
    )
    filter_params = {
        "project": _project["id"],
        "sim": dataset_config.sim["id"],
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
        print("\t(no premade SimRuns matching filter)")
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


@add_newline
def generate(
    dataset_config: DatasetConfig,
    num_datapoints: int = 10,
    materialize: bool = False,
    datapoint_callback=None,
):
    """
    Generate a dataset.
    Args:
        dataset_config: Specification for a Sim and its configurable parameters.
        num_datapoints: Number of datapoints in the dataset. A datapoint is an instant in time composed of all
                              the output images (rgb, iseg, cseg, etc) along with the annotations.
        materialize: Optionally download the dataset.
    Returns:
        None
    """
    hash = dataset_config.hash
    sim_name = dataset_config._sim["name"]
    internal_dataset_name = f"{sim_name}-{hash}-{num_datapoints}"
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
            "sim": dataset_config.sim["id"],
            "config": json.dumps(dataset_config.config),
            "amount": num_datapoints,
        },
        headers=auth_header(_auth_token),
    )
    print("Generating dataset:")
    print(json.dumps(dataset, indent=4, sort_keys=True))
    if materialize:
        print("Materialize requested, waiting until dataset finishes to download it.")
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
                    "\r{}".format(
                        f"Dataset<{dataset['name']}> not ready for download in state {dataset['state']}. "
                        f"SimRuns READY: {num_ready_simruns}/{num_simruns}. "
                        f"Checking again in {(next_check_datetime - datetime.now()).seconds}s."
                    ),
                    end="",
                )
                time.sleep(1)
            clear_last_print()
            print("\r{}".format("Checking dataset..."))
            dataset = get(
                f"{_base_url}/api/v1/datasets/{dataset['id']}/",
                headers=auth_header(_auth_token),
            ).json()

        if dataset["state"] == "READY":
            print("Dataset is ready for download.")
            dataset_download_res = get(
                f"{_base_url}/api/v1/datasets/{dataset['id']}/download/",
                headers=auth_header(_auth_token),
            ).json()
            name_slug = (
                f"{str(dataset['name']).replace(' ', '_')}-{dataset['id'][:8]}.zip"
            )
            # Throw it in /tmp for now I guess
            output_path = join(DATASET_OUTPUT_PATH, name_slug)
            existing_files = listdir(DATASET_OUTPUT_PATH)
            if name_slug not in existing_files:
                print(
                    f"Downloading {convert_size(dataset_download_res['size_bytes'])} dataset to {output_path}"
                )
                download_url(dataset_download_res["redirect_link"], output_path)
                process_zipped_dataset(output_path, datapoint_callback)
                print("Done.")
            else:
                print(
                    f"Download failed. Dataset {name_slug} already exists in {output_path}."
                )

        else:
            print(
                f"Dataset is no longer running but cannot be downloaded with state = {dataset['state']}"
            )

    return Dataset(dataset["name"], dataset)


class Dataset:
    _dataset = None

    @require_zpy_init
    def __init__(self, name: str = None, dataset: dict = None):
        """
        Construct a Dataset which is a local representation of a Dataset generated on the API.

        Args:
            name: If provided, Dataset will be automatically retrieved from the API.
            dataset: If Dataset has already been retrieved from the API, provide this.
        Returns
            Dataset
        """
        self._name = name

        if dataset is not None:
            self._dataset = dataset
        else:
            unique_dataset_filters = {
                "project": _project["id"],
                "name": name,
            }
            datasets = get(
                f"{_base_url}/api/v1/datasets/",
                params=unique_dataset_filters,
                headers=auth_header(_auth_token),
            ).json()["results"]
            self._dataset = datasets[0]

    @property
    def id(self):
        return self._dataset["id"]

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

    def view(self):
        return
