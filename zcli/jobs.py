from zcli.utils import auth_headers
from table_logger import TableLogger
import requests
import json
import logging

log = logging.getLogger(__name__)


class FetchFailed(Exception):
    pass


def fetch_jobs(endpoint, token):
    """ fetch all datasets in ragnarok """
    endpoint = f'{endpoint}/api/v1/jobs/'
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed('Unable to fetch jobs')
    jobs = json.loads(r.text)['results']
    tbl = TableLogger(columns='state,name,operation,created',default_colwidth=30)
    if len(jobs) == 0:
        log.info(None)
    for j in jobs:
        tbl(j['state'], j['name'], j['operation'], j['created_at'])
