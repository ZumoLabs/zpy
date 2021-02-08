from zcli.utils import auth_headers
from table_logger import TableLogger
import requests
import json
import logging


log = logging.getLogger(__name__)


class FetchFailed(Exception):
    pass


def fetch_scenes(endpoint, token):
    """ fetch all datasets in ragnarok """
    endpoint = f'{endpoint}/api/v1/scenes/'
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        raise FetchFailed('Unable to fetch scenes')
    scenes = json.loads(r.text)['results']
    tbl = TableLogger(columns='state,name,zpy_version,blender_version,created',default_colwidth=30)
    if len(scenes) == 0:
        log.info(None)
    for s in scenes:
        tbl(s['state'], s['name'], s['zpy_version'], s['blender_version'], s['created_at'])
