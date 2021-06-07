import json

import requests

from cli.utils import download_url, fetch_auth, parse_filter
from zpy.files import to_pathlib_path

DATASET_TYPES = ["uploaded-data-sets", "generated-data-sets", "job-data-sets"]


@fetch_auth
def filter_datasets(dfilter, project, url, auth_headers):
    """filter datasets

    Filter dataset objects on ZumoLabs backend by given dfilter.
    Parse dfilter using parse_filter and make calls to
    generated, uploaded, job dataset endpoints.

    Args:
        dfilter (str): filter query for datasets
        project (str): project uuid
        url (str): backend endpoint
        auth_headers: authentication for backend

    Return:
        dict: filtered datasets by dfilter
        {
            'uploaded-data-sets': {'id': 'name'},
            'generated-data-sets': {'id': 'name'},
            'job-data-sets': {'id': 'name'},
        }
    """
    filtered_datasets = {key: {} for key in DATASET_TYPES}
    field, pattern, regex = parse_filter(dfilter)
    for dataset_type in DATASET_TYPES:
        endpoint = f"{url}/api/v1/{dataset_type}/"
        params = {
            "project": project,
            f"{field}__{pattern}": regex,
        }

        # Do initial request
        r = requests.get(endpoint, params=params, headers=auth_headers)
        if r.status_code != 200:
            r.raise_for_status()
        body = json.loads(r.text)
        for data_set in body["results"]:
            filtered_datasets[dataset_type][data_set["id"]] = data_set["name"]

        # Traverse the next links until we've gotten all of the data sets
        while body["next"] is not None:
            r = requests.get(body["next"], headers=auth_headers)
            if r.status_code != 200:
                r.raise_for_status()
            body = json.loads(r.text)
            for data_set in body["results"]:
                filtered_datasets[dataset_type][data_set["id"]] = data_set["name"]

    return filtered_datasets


@fetch_auth
def create_generated_dataset(name, sim_name, config, project, url, auth_headers):
    """create dataset

    Create generated dataset on ZumoLabs backend which will launch
    a generation job with specified params.

    Args:
        name (str): name of dataset
        sim_name (str): name of sim the dataset is built from
        config (dict): configration of sim for this dataset
        project (str): project uuid
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/sims/"
    r = requests.get(endpoint, params={"name": sim_name}, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    if response["count"] != 1:
        raise NameError(f"found {response['count']} sims for name {sim_name}")
    sim = response["results"][0]
    endpoint = f"{url}/api/v1/generated-data-sets/"
    r = requests.post(
        endpoint,
        data={
            "project": project,
            "sim": sim["id"],
            "config": json.dumps(config),
            "name": name,
        },
        headers=auth_headers,
    )
    if r.status_code != 201:
        r.raise_for_status()


@fetch_auth
def create_uploaded_dataset(name, path, project, url, auth_headers):
    """upload dataset

    Upload dataset to S3 through ZumoLabs backend and
    create object.

    Args:
        name (str): name of dataset
        path (str): path to dataset
        project (str): project uuid
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/uploaded-data-sets/"
    r = requests.post(
        endpoint,
        data={"name": name, "project": project},
        files={"file": open(path, "rb")},
        headers=auth_headers,
    )
    if r.status_code != 201:
        r.raise_for_status()


@fetch_auth
def download_dataset(name, path, dataset_type, url, auth_headers):
    """download dataset

    Download dataset object from S3 through ZumoLabs backend.

    Args:
        name (str): name of dataset to download
        path (str): output directory
        dataset_type (str): type of dataset to download
        url (str): backend endpoint
        auth_headers: authentication for backend

    Returns:
        str: output file path
    """
    endpoint = f"{url}/api/v1/{dataset_type}-data-sets/"
    r = requests.get(endpoint, params={"name": name}, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    if response["count"] != 1:
        raise NameError(f"found {response['count']} datasets for name {name}")
    dataset = response["results"][0]
    endpoint = (
        f"{url}/api/v1/{dataset['dataset_type']}-data-sets/{dataset['id']}/download"
    )
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    name_slug = f"{dataset['name'].replace(' ', '_')}-{dataset['id'][:8]}.zip"
    output_path = to_pathlib_path(path) / name_slug
    download_url(response["redirect_link"], output_path)
    return output_path


def fetch_datasets(filters):
    """fetch datasets

    Fetch dataset objects from ZumoLabs backend. Fetches all three
    datasets types uploaded, generated, and job.

    Args:
        filters (dict): query param filters for API call
    Returns:
        list: paginated sorted datasets for all types
    """
    datasets = []
    for dataset_type in DATASET_TYPES:
        short_dataset_type = dataset_type.split("-")[0]
        datasets += [
            (lambda d: d.update({"type": short_dataset_type}) or d)(d)
            for d in _fetch_type_datasets(dataset_type, filters)
        ]
    return sorted(datasets, key=lambda i: i["created_at"], reverse=True)


@fetch_auth
def _fetch_type_datasets(dataset_type, filters, url, auth_headers):
    """fetch type of datasets

    Args:
        dataset_type (str): type of dataset to fetch
        filters (dict): query param filters for API call
        url (str): backend endpoint
        auth_headers: authentication for backend

    Returns:
        list: paginated datasets for given type
    """
    endpoint = f"{url}/api/v1/{dataset_type}/"
    r = requests.get(endpoint, headers=auth_headers, params=filters)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)["results"]
