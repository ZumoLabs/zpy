from cli.utils import fetch_auth
import requests
import json


@fetch_auth
def create_transform(name, operation, config, project, url, auth_headers):
    """create transform

    Create a job object on ZumoLabs backend. This will trigger the backend
    to run the job.

    Args:
        name (str): name of dataset
        operation (str): transform type
        config (dict): configuration for transform
        project (str): project uuid
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    from cli.datasets import fetch_dataset

    dataset = fetch_dataset(name)
    endpoint = f"{url}/api/v1/transforms/"
    data = {
        "project": project,
        "operation": operation,
        "name": name,
        "input_dataset": dataset["id"],
        "config": json.dumps(config),
    }
    r = requests.post(endpoint, data=data, headers=auth_headers)
    if r.status_code != 201:
        r.raise_for_status()


@fetch_auth
def fetch_transforms(filters, url, auth_headers):
    """fetch transforms

    Fetch transform objects from ZumoLabs backend.

    Args:
        filters (dict): query param filters for API call
        url (str): backend endpoint
        auth_headers: authentication for backend

    Returns:
        list: list of transforms
    """
    endpoint = f"{url}/api/v1/transforms/"
    r = requests.get(endpoint, headers=auth_headers, params=filters)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)["results"]


@fetch_auth
def available_transforms(url, auth_headers):
    """available transforms

    List all transforms available on the backend.

    Args:
        url (str): backend endpoint
        auth_headers: authentication for backend

    Returns:
        list: list of transforms
    """
    endpoint = f"{url}/api/v1/transforms/available/"
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)
