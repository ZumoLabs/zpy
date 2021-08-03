import functools
import json
import time
from datetime import datetime, timedelta
from os import listdir
from pathlib import Path
from typing import Dict
from typing import Union
from uuid import UUID

import requests.exceptions
from pydash import set_, unset, is_empty, pascal_case

from cli.utils import download_url
from zpy.client_util import (
    add_newline,
    get,
    post,
    convert_size,
    auth_header,
    clear_last_print,
    convert_to_rag_query_params,
    is_done,
    format_dataset,
    dict_hash,
)

_init_done: bool = False
_auth_token: str = ""
_base_url: str = ""
_version: str = ""
_versioned_url: str = ""
_project: Union[Dict, None] = None


class InvalidAuthTokenError(Exception):
    """Raised when an auth_token is missing or invalid."""

    pass


class InvalidProjectError(Exception):
    """Raised when accessing a project which does not exist or without appropriate access permissions."""

    pass


class ClientNotInitializedError(Exception):
    """Raised when trying to use functionality which is dependent on calling client.init()"""

    pass


class InvalidSimError(Exception):
    """Raised when a Sim asked for by name cannot be found."""


def init(
    auth_token: str = "",
    project_uuid: str = "",
    base_url: str = "https://ragnarok.zumok8s.org",
    version: str = "v2",
):
    """
    Initializes the zpy client library.

    Args:
        auth_token (str): API auth_token. Required for all internal API calls.
        project_uuid (str): A valid uuid4 project id. Required to scope permissions for all requested API objects.
        base_url (str, optional): API url. Overridable for testing different environments.
        version (str, optional): API version. Overridable for testing different API versions. Defaults to the most
                                 recent version.
    Returns:
        None: No return value.
    """
    global _init_done, _auth_token, _base_url, _version, _versioned_url, _project
    _auth_token = auth_token
    _base_url = base_url
    _version = version
    _versioned_url = f"{base_url}/api/{version}"

    try:
        UUID(project_uuid, version=4)
    except ValueError:
        raise InvalidProjectError(
            "Init failed: project_uuid must be a valid uuid4 string."
        ) from None

    if is_empty(auth_token):
        raise InvalidAuthTokenError(
            f"Init failed: invalid auth token - find yours at https://app.zumolabs.ai/settings/auth-token."
        )

    try:
        _project = get(
            f"{_versioned_url}/projects/{project_uuid}",
            headers=auth_header(_auth_token),
        ).json()
        _init_done = True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise InvalidAuthTokenError(
                f"Init failed: invalid auth token - find yours at https://app.zumolabs.ai/settings/auth-token."
            ) from None
        elif e.response.status_code == 404:
            raise InvalidProjectError(
                "Init failed: you are not part of this project or it does not exist."
            ) from None


DATASET_OUTPUT_PATH = Path("/tmp")  # for generate and default_saver_func


def require_zpy_init(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not _init_done:
            raise ClientNotInitializedError(
                "Client not initialized: project and auth_token must be set via client.init()."
            ) from None
        return func(*args, **kwargs)

    return wrapper


DYNAMIC_ATTRIBUTES_KEY = "_dynamic_attributes"
DYNAMIC_ATTRIBUTE_GIN_PREFIX = "run."


class DatasetConfig:
    def __init__(self, *args, **kwargs):
        # Placeholders to make IDEs happy. Actual value setting happens in the from_sim_name factory method.
        self._sim = None
        self._config = {}
        raise RuntimeWarning(
            "DatasetConfig is not directly instantiable any more. Use DatasetConfig.from_sim_name!"
        )

    @classmethod
    @require_zpy_init
    def from_sim_name(cls, sim_name: str):
        """Create a Sim specific DatasetConfig with instance attributes corresponding to adjustable Sim parameters.

        Args:
            sim_name (str): The name of the Sim.
        """
        unique_sim_filters = {
            "project": _project["id"],
            "name": sim_name,
        }
        sims = get(
            f"{_versioned_url}/sims/",
            params=unique_sim_filters,
            headers=auth_header(_auth_token),
        ).json()["results"]
        if len(sims) == 1:
            print(f"Found Sim<{sim_name}> in Project<{_project['name']}>")
            sim = sims[0]
        else:
            raise InvalidSimError(
                f"Could not find Sim<{sim_name}> in Project<{_project['name']}>."
            )

        # Add the run_kwargs as attributes to the class
        dynamic_attributes = {DYNAMIC_ATTRIBUTES_KEY: []}
        for run_kwarg in sim["run_kwargs"]:
            property_name = run_kwarg["name"]
            internal_name = f"_{property_name}"
            # The extra _internal_name kwarg is to capture the value of internal_name at that point in the loop,
            # otherwise every property from this loop will refer to the same thing.
            p = property(
                fget=lambda _self, _internal_name=internal_name: getattr(
                    _self, _internal_name
                ),
                fset=lambda _self, value, _internal_name=internal_name: setattr(
                    _self, _internal_name, value
                ),
                doc=f"Type: {run_kwarg['type']}. Default if not set: {run_kwarg['default']}.",
            )
            # Add underscore-prefixed name for storing the actual value
            dynamic_attributes[internal_name] = None
            # Add non-underscored name to be treated as a @property
            dynamic_attributes[property_name] = p
            # Keep track of all of the dynamic attributes that were added this way (used for adding to the config later)
            dynamic_attributes[DYNAMIC_ATTRIBUTES_KEY].append(property_name)

        def constructor(self, sim):
            """Override DatasetConfig constructor in order to not refetch the same Sim.

            Args:
                sim (dict): Sim object fetched from backend API.
            """
            self._sim = sim
            self._config = {}

        # creating class dynamically
        class_name = pascal_case(sim["name"]) + "DatasetConfig"
        clazz = type(
            class_name,
            (DatasetConfig,),
            {
                "__init__": constructor,
                "__doc__": sim["description"],
                **dynamic_attributes,
            },
        )
        return clazz(sim)

    @property
    def sim(self):
        """
        Returns:
            dict: The Sim object.
        """
        return self._sim

    @property
    def config(self):
        """
        Property which holds the parameters managed via DatasetConfig.set() and DatasetConfig.unset()

        Returns:
            dict: A dict representing a json object of gin config parameters.
        """
        dynamic_attr_values = {}
        for dynamic_attr in getattr(self, DYNAMIC_ATTRIBUTES_KEY, []):
            dynamic_attr_value = getattr(self, dynamic_attr)
            if dynamic_attr_value is not None:
                dynamic_attr_values[
                    DYNAMIC_ATTRIBUTE_GIN_PREFIX + dynamic_attr
                ] = dynamic_attr_value

        return {
            **self._config,
            **dynamic_attr_values,
        }

    @property
    def hash(self):
        """Return a hash of the config."""
        return dict_hash(self._config)

    def set(self, path: str, value: any):
        """Set a configurable parameter. Uses pydash.set_.

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
        """Remove a configurable parameter. Uses pydash.unset.

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

    filter_params = {
        "project": _project["id"],
        "sim": dataset_config.sim["id"],
        "state": "READY",
        "page-size": num_samples,
        **convert_to_rag_query_params(dataset_config.config, "config"),
    }
    simruns_res = get(
        f"{_versioned_url}/simruns/",
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
        f"{_versioned_url}/files/",
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
    materialize: bool = True,
    datapoint_callback=None,
):
    """
    Generate a dataset.
    Args:
        dataset_config (DatasetConfig): Specification for a Sim and its configurable parameters.
        num_datapoints (int): Number of datapoints in the dataset. A datapoint is an instant in time composed of all
                              the output images (rgb, iseg, cseg, etc) along with the annotations.
        datapoint_callback (fn): Callback function to be called with every datapoint in the generated Dataset.
        materialize (bool): Optionally download the dataset. Defaults to True.
    Returns:
        None: No return value.
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
                "sim": dataset_config.sim["id"],
                "config": json.dumps(dataset_config.config),
                "amount": num_datapoints,
            },
            headers=auth_header(_auth_token),
        )
        print("Generating dataset:")
        print(json.dumps(dataset, indent=4, sort_keys=True))
    else:
        dataset = datasets_res["results"][0]

    if materialize:
        print("Materialize requested, waiting until dataset finishes to download it.")
        dataset = get(
            f"{_versioned_url}/datasets/{dataset['id']}/",
            headers=auth_header(_auth_token),
        ).json()
        while not is_done(dataset["state"]):
            all_simruns_query_params = {"datasets": dataset["id"]}
            num_simruns = get(
                f"{_versioned_url}/simruns/",
                params=all_simruns_query_params,
                headers=auth_header(_auth_token),
            ).json()["count"]
            num_ready_simruns = get(
                f"{_versioned_url}/simruns/",
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
            print("Checking dataset...", end="\r")
            dataset = get(
                f"{_versioned_url}/datasets/{dataset['id']}/",
                headers=auth_header(_auth_token),
            ).json()

        if dataset["state"] == "READY":
            print("Dataset is ready for download.")
            dataset_download_res = get(
                f"{_versioned_url}/datasets/{dataset['id']}/download/",
                headers=auth_header(_auth_token),
            ).json()
            name_slug = (
                f"{str(dataset['name']).replace(' ', '_')}-{dataset['id'][:8]}.zip"
            )
            # Throw it in /tmp for now I guess
            output_path = Path(DATASET_OUTPUT_PATH) / name_slug
            existing_files = listdir(DATASET_OUTPUT_PATH)
            if name_slug not in existing_files:
                print(
                    f"Downloading {convert_size(dataset_download_res['size_bytes'])} dataset to {output_path}"
                )
                download_url(dataset_download_res["redirect_link"], output_path)
                format_dataset(output_path, datapoint_callback)
                print("Done.")
            elif datapoint_callback is not None:
                format_dataset(output_path, datapoint_callback)
            else:
                print(f"Dataset {name_slug} already exists in {output_path}.")

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
                f"{_versioned_url}/datasets/",
                params=unique_dataset_filters,
                headers=auth_header(_auth_token),
            ).json()["results"]
            self._dataset = datasets[0]

    @property
    def id(self):
        """
        Returns:
            str: The Dataset's unique identifier.
        """
        return self._dataset["id"]

    @property
    def name(self):
        """
        Returns:
            str: The Dataset's name.
        """
        return self._name

    @property
    def state(self):
        """
        Returns:
            str: The Dataset's state.
        """
        if not self._dataset:
            print("Dataset needs to be generated before you can access its state.")
        return self._dataset["state"]
