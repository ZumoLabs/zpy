from cli.utils import auth_headers
from table_logger import TableLogger
import requests
import json
import logging

log = logging.getLogger(__name__)


def create_new_job(name, operation, config, datasets, url, token):
    """ create job on ragnarok """
    endpoint = f'{url}/api/v1/jobs/'
    data = {
        'operation': operation,
        'name': name,
        'input_data_sets': datasets,
        'config': json.dumps(config)
    }
    r = requests.post(endpoint, data=data, headers=auth_headers(token))
    if r.status_code != 201:
        log.warning(f'Unable to create {operation} job {name} on datasets {datasets}')
        return
    log.info(f'created {operation} job {name} {config} on datasets {datasets}')


def fetch_jobs(endpoint, token):
    """ fetch all datasets in ragnarok """
    endpoint = f'{endpoint}/api/v1/jobs/'
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        log.warning('Unable to fetch jobs')
        return
    jobs = json.loads(r.text)['results']
    tbl = TableLogger(columns='state,name,operation,created',default_colwidth=30)
    if len(jobs) == 0:
        log.info(None)
    for j in jobs:
        tbl(j['state'], j['name'], j['operation'], j['created_at'])
