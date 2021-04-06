from cli.utils import fetch_auth, download_url
from zpy.files import to_pathlib_path
from table_logger import TableLogger
import requests
import json
import logging


log = logging.getLogger(__name__)


@fetch_auth
def create_sim(name, path, url, auth_headers):
    """ upload a local sim to ragnarok """
    endpoint = f'{url}/api/v1/sims/'
    data = {'name': name}
    files = {'file': open(path, 'rb')}
    r = requests.post(endpoint, data=data, headers=auth_headers, files=files)
    if r.status_code != 201:
        log.warning(f'unable to create sim {name} from {path}')
        return
    log.info(f'created sim {name} from {path}')


@fetch_auth
def fetch_sim(name, path, url, auth_headers):
    """ fetch a sim from ragnarok """
    endpoint = f'{url}/api/v1/sims/'
    params = {'name': name}
    r = requests.get(endpoint, params=params, headers=auth_headers)
    if r.status_code != 200:
        log.warning(f'Unable to fetch sims')
        return
    response = json.loads(r.text)
    if response['count'] != 1:
        log.warning(f'Unable to find sim with name "{name}"')
        return
    sim = response['results'][0]
    endpoint = f"{url}/api/v1/sims/{sim['id']}/download"
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        log.warning(f"Unable to get download link for sim {sim['id']}")
        return
    response = json.loads(r.text)
    name_slug = f"{sim['name'].replace(' ', '_')}-{sim['id'][:8]}.zip"
    output_path = to_pathlib_path(path) / name_slug
    download_url(response['redirect_link'], output_path)


@fetch_auth
def fetch_sims(url, auth_headers):
    """ fetch all datasets in ragnarok """
    endpoint = f'{url}/api/v1/sims/'
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        log.warning('Unable to fetch sims')
        return
    sims = json.loads(r.text)['results']
    tbl = TableLogger(
        columns='state,name,zpy_version,blender_version,created', default_colwidth=30)
    if len(sims) == 0:
        log.info(None)
    for s in sims:
        tbl(s['state'], s['name'], s['zpy_version'],
            s['blender_version'], s['created_at'])
