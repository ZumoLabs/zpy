import functools
import json
from random import randrange

import requests

_auth_token: str = ""
_base_url: str = ""


def init(auth_token: str, base_url: str = "http://localhost:8000", **kwargs):
    global _auth_token, _base_url
    _auth_token = auth_token
    _base_url = base_url


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


def get(url, **kwargs):
    """Call any rag API url while adding the auth header automatically. Takes any arbitrary requests.get kwargs.

    Args:
        url (str): Ragnarok API url
        kwargs: Forwarded to the requests.get function call
    Returns:
        deserialized API response
    """
    headers = {
        **(kwargs["headers"] if "headers" in kwargs else {}),
        "Authorization": f"Token {_auth_token}",
    }
    r = requests.get(url, headers=headers, **kwargs)
    if r.status_code != 200:
        if r.status_code == 400:
            # Known error
            print(r.json())
        else:
            r.raise_for_status()

    return r.json()


class Dataset:
    def __init__(self, project_uuid: str, sim_uuid: str, **kwargs):
        self._project_uuid = project_uuid
        self._sim_uuid = sim_uuid
        self._sim = None

        # Data set generic or "standard" properties. None is reserved for the unset value or "use defaults".
        self._jitter_material = None
        self._jitter_mesh = None
        self._bool_prop = None
        self._test_val_1 = None
        self._a__b1__c0 = None

        # Data set custom or "sim specific" properties.
        self._sim_specific_params = {}

    @add_newline
    def show_params(self):
        if self._sim is None:
            endpoint = f"{_base_url}/api/v1/sims/{self._sim_uuid}/"
            headers = {"Authorization": f"Token {_auth_token}"}
            r = requests.get(endpoint, headers=headers)
            if r.status_code != 200:
                r.raise_for_status()
            self._sim = r.json()
        print(f"Available params for Sim:{self._sim_uuid}:<{self._sim['name']}>")
        print(json.dumps(self._sim["run_kwargs"], indent=4, sort_keys=True))

    @property
    def jitter_material(self):
        return self._jitter_material

    @jitter_material.setter
    def jitter_material(self, value: bool):
        self._jitter_material = value

    @property
    def jitter_mesh(self):
        return self._jitter_mesh

    @jitter_mesh.setter
    def jitter_mesh(self, value: bool):
        self._jitter_mesh = value

    @property
    def bool_prop(self):
        return self._bool_prop

    @bool_prop.setter
    def bool_prop(self, value: bool):
        self._bool_prop = value

    @property
    def test_val_1(self):
        return self._test_val_1

    @test_val_1.setter
    def test_val_1(self, value: str):
        self._test_val_1 = value

    @property
    def cool_nested_prop(self):
        return self._a__b1__c0

    @cool_nested_prop.setter
    def cool_nested_prop(self, value: str):
        self._a__b1__c0 = value

    @property
    def sim_specific_params(self):
        """Use add_sim_specific_param and remove_sim_specific_param to manage."""
        return self._sim_specific_params

    def add_sim_specific_param(self, key, value):
        """Key should be the flattened gin config field as described in _config."""
        self._sim_specific_params[key] = value

    def remove_sim_specific_param(self, key):
        """Key should be the flattened gin config field as described in _config."""
        self._sim_specific_params.pop(key, None)

    @property
    def _config(self):
        """Returns a dict of gin config values pre-flattened by using django field traversal notation.
        Ex:
        {
            "fieldA": "a",
            "fieldB1": {
                "fieldB2": "b",
                "fieldC1: {
                    "fieldC2": "c"
                }
            }
        }
        ->
        {
            "fieldA": "a",
            "fieldB1__fieldB2": "b",
            "fieldB1__fieldC1__fieldC2: "c"
        }
        """
        return {
            "sim": self._sim,
            "jitter_mesh": self.jitter_mesh,
            "jitter_material": self.jitter_material,
            "bool_prop": self.bool_prop,
            "test_val_1": self.test_val_1,
            "A__B.1__C.0": self.cool_nested_prop,
            **self.sim_specific_params,
        }

    @add_newline
    def preview(self, num_samples=10):
        print(f"Generating preview for config:")
        print(json.dumps(self._config, indent=4, sort_keys=True))

        filter_params = {
            "project": self._project_uuid,
            "sim": self._sim_uuid,
            "state": "READY",
            "config": to_query_param_value(self._config),
        }
        data_sets = get(
            f"{_base_url}/api/v1/generated-data-sets/", params=filter_params
        )["results"]

        if len(data_sets) == 0:
            print(f"No preview available.")
            print("\t(no premade data sets)")
            return

        # Choose random data set in page
        data_set_id = data_sets[randrange(len(data_sets))]["id"]
        # Re-request the data set detail (image links aren't included in the list call
        data_set = get(f"{_base_url}/api/v1/generated-data-sets/{data_set_id}/")
        if len(data_set["images"]) == 0:
            print(f"No preview available.")
            print("\t(no images found)")
            return

        bounded_num_samples = min([len(data_set["images"]), num_samples])
        formatted_samples = {}
        found_images = 0
        for sample in data_set["images"]:
            if sample["name"].startswith("_plot"):
                continue

            image_category, name, output_type = sample["name"].split(".")

            if name not in formatted_samples:
                formatted_samples[name] = {}

            formatted_samples[name][output_type] = sample["data"]
            found_images += 1

            if found_images == bounded_num_samples:
                # Not pulling next page for now. Either find enough samples or we don't.
                break

        print(json.dumps(formatted_samples, indent=4, sort_keys=True))

    @add_newline
    def generate(self, name):
        # Pretty hacky. Grab existing data sets that exist for current project/sim and just increment the number to
        # auto-name them.
        query_params = {
            "project": self._project_uuid,
            "sim": self._sim_uuid,
            "name__startswith": name,
            "ordering": "-created_at",
        }
        data_sets = get(
            f"{_base_url}/api/v1/generated-data-sets/", params=query_params
        )["results"]
        latest_id = data_sets[0]["name"][(len(name) + 1) :]

        endpoint = f"{_base_url}/api/v1/generated-data-sets/"
        r = requests.post(
            endpoint,
            data={
                "project": self._project_uuid,
                "sim": self._sim_uuid,
                "config": json.dumps(remove_none_values(self._config)),
                "name": name + f".{int(latest_id) + 1}",
            },
            headers={"Authorization": f"Token {_auth_token}"},
        )
        if r.status_code != 201:
            if r.status_code == 400:
                # Known error
                print(r.json())
            else:
                r.raise_for_status()

        print("Requested new data set:")
        print(json.dumps(r.json(), indent=4, sort_keys=True))
        print(
            f"You can follow its progress at app.zumolabs.ai/sims/{self._sim_uuid}/batches"
        )


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


def remove_none_values(obj):
    return {k: v for k, v in obj.items() if v is not None}
