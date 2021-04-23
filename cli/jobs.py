from cli.utils import fetch_auth
from table_logger import TableLogger
import requests
import json
import logging

log = logging.getLogger(__name__)


@fetch_auth
def create_new_job(name, operation, config, datasets, url, auth_headers):
    """ create job on ragnarok """
    endpoint = f'{url}/api/v1/jobs/'
    data = {
        'operation': operation.upper(),
        'name': name,
        'input_data_sets': datasets,
        'config': json.dumps(config)
    }
    r = requests.post(endpoint, data=data, headers=auth_headers)
    if r.status_code != 201:
        log.warning(f'Unable to create {operation} job {name} on datasets {datasets}')
        return
    log.info(f'created {operation} job {name} {config} on datasets {datasets}')


@fetch_auth
def fetch_jobs(url, auth_headers):
    """ fetch jobs

    Fetch job objects from ZumoLabs backend.

    Args:
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f'{url}/api/v1/jobs/'
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)['results']
