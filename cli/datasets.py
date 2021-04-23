import json
import logging

import requests
from table_logger import TableLogger
from zpy.files import to_pathlib_path

from cli.utils import download_url, fetch_auth, parse_dataset_filter

log = logging.getLogger(__name__)


@fetch_auth
def create_generated_dataset(name, sim_name, config, url, auth_headers):
    """ create a dataset on ragnarok """
    endpoint = f'{url}/api/v1/sims/'
    params = {'name': sim_name}
    r = requests.get(endpoint, params=params, headers=auth_headers)
    if r.status_code != 200:
        log.warning(f'unable to fetch sims')
        return
    response = json.loads(r.text)
    if response['count'] != 1:
        log.warning(f'unable to find sim with name {sim_name}')
        return
    sim = response['results'][0]
    endpoint = f'{url}/api/v1/generated-data-sets/'
    data = {
        'sim': sim['id'],
        'config': json.dumps(config),
        'name': name
    }
    r = requests.post(endpoint, data=data, headers=auth_headers)
    if r.status_code != 201:
        log.warning(
            f'Unable to create dataset {name} for sim {sim_name} with config {config}')
        return
    log.info(f'created dataset {name} for sim {sim_name} with config {config}')


@fetch_auth
def filter_dataset(dfilter, url, auth_headers):
    """ filter dataset """
    dset = []
    field, pattern, regex = parse_dataset_filter(dfilter)
    endpoint = f'{url}/api/v1/uploaded-data-sets/'
    dset.extend(filter_dataset_url(
        field, pattern, regex, endpoint, auth_headers))
    endpoint = f'{url}/api/v1/generated-data-sets/'
    dset.extend(filter_dataset_url(
        field, pattern, regex, endpoint, auth_headers))
    endpoint = f'{url}/api/v1/job-data-sets/'
    dset.extend(filter_dataset_url(
        field, pattern, regex, endpoint, auth_headers))
    return dset


def filter_dataset_url(field, pattern, regex, url, auth_headers):
    """ filter generated dataset """
    endpoint = f'{url}?{field}__{pattern}={regex}'
    datasets, names = [], []
    while endpoint is not None:
        r = requests.get(endpoint, headers=auth_headers)
        if r.status_code != 200:
            log.warning(f"Unable to filter {endpoint}")
            return []
        response = json.loads(r.text)
        for d in response['results']:
            names.append(d['name'])
            datasets.append(d['id'])
        endpoint = response['next']
    log.info(f'filter <{url}> found {names}')
    return datasets


@fetch_auth
def create_uploaded_dataset(name, path, url, auth_headers):
    """ upload dataset

    Upload dataset to S3 through ZumoLabs backend and 
    create object.

    Args:
        name (str): name of dataset
        path (str): path to dataset
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f'{url}/api/v1/uploaded-data-sets/'
    r = requests.post(
        endpoint, 
        data={'name': name},
        files={'file': open(path, 'rb')},
        headers=auth_headers)
    if r.status_code != 201:
        r.raise_for_status()


@fetch_auth
def download_dataset(name, path, dataset_type, url, auth_headers):
    """ download dataset

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
    endpoint = f'{url}/api/v1/{dataset_type}-data-sets/'
    r = requests.get(endpoint, params={'name': name}, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    if response['count'] != 1:
        raise NameError(f"found {response['count']} datasets for name {name}")
    dataset = response['results'][0]
    endpoint = f"{url}/api/v1/{dataset['dataset_type']}-data-sets/{dataset['id']}/download"
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    name_slug = f"{dataset['name'].replace(' ', '_')}-{dataset['id'][:8]}.zip"
    output_path = to_pathlib_path(path) / name_slug
    download_url(response['redirect_link'], output_path)
    return output_path


def fetch_datasets():
    """ fetch datasets

    Fetch dataset objects from ZumoLabs backend. Fetches all three 
    datasets types uploaded, generated, and job.

    Returns:
        list: paginated sorted datasets for all types
    """
    datasets = []
    datasets += [(lambda d: d.update({'type': 'job'}) or d)(d) 
        for d in _fetch_type_datasets('job-data-sets')]
    datasets += [(lambda d: d.update({'type': 'generated'}) or d)(d) 
        for d in _fetch_type_datasets('generated-data-sets')]
    datasets += [(lambda d: d.update({'type': 'uploaded'}) or d)(d) 
        for d in _fetch_type_datasets('uploaded-data-sets')]
    return sorted(datasets, key = lambda i: i['created_at'], reverse=True)


@fetch_auth
def _fetch_type_datasets(dataset_type, url, auth_headers):
    """ fetch type of datasets

    Args:
        dataset_type (str): type of dataset to fetch
        url (str): backend endpoint
        auth_headers: authentication for backend

    Returns:
        list: paginated datasets for given type
    """
    endpoint = f'{url}/api/v1/{dataset_type}/'
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)['results']
