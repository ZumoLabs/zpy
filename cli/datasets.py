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
    """ uploaded a dataset to ragnarok """
    endpoint = f'{url}/api/v1/uploaded-data-sets/'
    data = {'name': name}
    files = {'file': open(path, 'rb')}
    r = requests.post(endpoint, data=data, headers=auth_headers, files=files)
    if r.status_code != 201:
        log.warning(f'unable to create dataset {name} from {path}')
        return
    log.info(f'created dataset {name} from {path}')


@fetch_auth
def fetch_dataset(name, path, dataset_type, url, auth_headers):
    """ fetch a dataset from ragnarok """
    endpoint = f'{url}/api/v1/{dataset_type}-data-sets/'
    params = {'name': name}
    r = requests.get(endpoint, params=params, headers=auth_headers)
    if r.status_code != 200:
        log.warning(f'Unable to fetch {dataset_type} datasets')
        return
    response = json.loads(r.text)
    if response['count'] != 1:
        log.warning(
            f'Unable to find {dataset_type} dataset with name "{name}"')
        return
    dataset = response['results'][0]
    endpoint = f"{url}/api/v1/{dataset['dataset_type']}-data-sets/{dataset['id']}/download"
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        log.warning(f"Unable to get download link for dataset {dataset['id']}")
        return
    response = json.loads(r.text)
    name_slug = f"{dataset['name'].replace(' ', '_')}-{dataset['id'][:8]}.zip"
    output_path = to_pathlib_path(path) / name_slug
    download_url(response['redirect_link'], output_path)


@fetch_auth
def fetch_uploaded_datasets(url, auth_headers):
    endpoint = f'{url}/api/v1/uploaded-data-sets/'
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        log.warning('Unable to fetch uploaded datasets')
        return []
    return json.loads(r.text)['results']


@fetch_auth
def fetch_generated_datasets(url, auth_headers):
    endpoint = f'{url}/api/v1/generated-data-sets/'
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        log.warning('Unable to fetch generated datasets')
        return []
    return json.loads(r.text)['results']


@fetch_auth
def fetch_job_datasets(url, auth_headers):
    endpoint = f'{url}/api/v1/job-data-sets/'
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        log.warning('Unable to fetch job datasets')
        return []
    return json.loads(r.text)['results']


def fetch_datasets():
    """ fetch all datasets in ragnarok """
    u_datasets = fetch_uploaded_datasets()
    g_datasets = fetch_generated_datasets()
    j_datasets = fetch_job_datasets()
    tbl = TableLogger(columns='state,type,name,timestamp,id',
                      default_colwidth=30)
    for d in u_datasets:
        tbl(d['state'], 'UPLOADED', d['name'], d['created_at'], d['id'])
    for d in g_datasets:
        tbl(d['state'], 'GENERATED', d['name'], d['created_at'], d['id'])
    for d in j_datasets:
        tbl(d['state'], 'JOB', d['name'], d['created_at'], d['id'])
