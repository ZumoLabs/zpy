from zcli.utils import auth_headers, download_url, to_pathlib_path
from table_logger import TableLogger
import requests
import logging
import json

log = logging.getLogger(__name__)


def create_dataset(name, scene, path, config, url, token):
    """ create a dataset on ragnarok """
    endpoint = f'{url}/api/v1/scenes/'
    params = {'name': scene}
    r = requests.get(endpoint, params=params, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed(f'Unable to fetch scenes')
    response = json.loads(r.text)
    if response['count'] != 1:
        raise FetchFailed(f'Unable to find scene with name {scene}')
    endpoint = f'{url}/api/v1/generated-data-sets/'
    data = {
        'scene': scene,
        'config': json.dumps(config),
        'name': name
    }
    r = requests.post(endpoint, data=data, heaers=auth_headers(token))
    if r.status_code != 200:
        raise CreateFailed(f'Unable to create dataset {name} for scene {scene} with config {config}')
    log.info(f'created dataset {name} for scene {scene} with config {config}')
    

def create_uploaded_dataset(name, path, url, token):
    """ uploaded a dataset to ragnarok """
    endpoint = f'{url}/api/v1/uploaded-data-sets/'
    data = {'name': name}
    files = {'file': open(path, 'rb')}
    r = requests.post(endpoint, data=data, headers=auth_headers(token), files=files)
    if r.status_code != 201:
        log.warning(f'unable to create dataset {name} from {path}')
        return
    log.info('created dataset {name} from {path}')


def fetch_dataset(name, path, dataset_type, url, token):
    """ fetch a dataset from ragnarok """
    endpoint = f'{url}/api/v1/{dataset_type}-data-sets/'
    params = {'name': name}
    r = requests.get(endpoint, params=params, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed(f'Unable to fetch {dataset_type} datasets')
    response = json.loads(r.text)
    if response['count'] != 1:
        raise FetchFailed(f'Unable to find {dataset_type} dataset with name "{name}"')
    dataset = response['results'][0]
    endpoint = f"{url}/api/v1/{dataset['dataset_type']}-data-sets/{dataset['id']}/download"
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed(f"Unable to get download link for dataset {dataset['id']}")
    response = json.loads(r.text)
    name_slug = f"{dataset['name'].replace(' ', '_')}-{dataset['id'][:8]}.zip"
    output_path = to_pathlib_path(path) / name_slug
    download_url(response['redirect_link'], output_path)


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
