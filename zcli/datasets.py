from zcli.utils import auth_headers
from table_logger import TableLogger
import requests
import logging
import json

log = logging.getLogger(__name__)


class FetchFailed(Exception):
    pass


class ModelNotFound(Exception):
    pass


def fetch_dataset(name, path, dataset_type, endpoint, token):
    """ fetch a dataset from ragnarok """
    endpoint = f'{endpoint}/api/v1/{dataset_type}-data-sets/'
    params = {'name': name}
    r = requests.get(endpoint, params=params, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed(f'Unable to fetch {dataset_type} datasets')
    response = json.loads(r.text)
    if response['count'] != 1:
        raise ModelNotFound(f'Unable to find {dataset_type} dataset with name "{name}"')
    dataset_id = response['results'][0]
    print (dataset_id)
    endpoint = f"{endpoint}/api/v1/data-sets/{response['results']['id']}/download"
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed(f"Unable to fetch dataset {response['results']['id']}")
    response = json.loads(r.text)
    print (response)


def fetch_datasets(endpoint, token):
    """ fetch all datasets in ragnarok """
    u_datasets = fetch_uploaded_datasets(endpoint, token)
    g_datasets = fetch_generated_datasets(endpoint, token)
    j_datasets = fetch_job_datasets(endpoint, token)
    tbl = TableLogger(columns='state,type,name,timestamp',default_colwidth=30)
    for d in u_datasets:
        tbl(d['state'], 'UPLOADED', d['name'], d['created_at'])
    for d in g_datasets:
        tbl(d['state'], 'GENERATED', d['name'], d['created_at'])
    for d in j_datasets:
        tbl(d['state'], 'JOB', d['name'], d['created_at'])


def fetch_uploaded_datasets(endpoint, token):
    endpoint = f'{endpoint}/api/v1/uploaded-data-sets/'
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed('Unable to fetch uploaded datasets')
    return json.loads(r.text)['results']


def fetch_generated_datasets(endpoint, token):
    endpoint = f'{endpoint}/api/v1/generated-data-sets/'
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed('Unable to fetch generated datasets')
    return json.loads(r.text)['results']


def fetch_job_datasets(endpoint, token):
    endpoint = f'{endpoint}/api/v1/job-data-sets/'
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed('Unable to fetch job datasets')
    return json.loads(r.text)['results']
