from cli.utils import auth_headers, download_url
from zpy.files import to_pathlib_path
from table_logger import TableLogger
import requests
import json
import logging


log = logging.getLogger(__name__)


def create_scene(name, path, url, token):
    """ upload a local scene to ragnarok """
    endpoint = f'{url}/api/v1/scenes/'
    data = {'name': name}
    files = {'file': open(path, 'rb')}
    r = requests.post(endpoint, data=data, headers=auth_headers(token), files=files)
    if r.status_code != 201:
        log.warning(f'unable to create scene {name} from {path}')
        return
    log.info(f'created scene {name} from {path}')


def fetch_scene(name, path, url, token):
    """ fetch a scene from ragnarok """
    endpoint = f'{url}/api/v1/scenes/'
    params = {'name': name}
    r = requests.get(endpoint, params=params, headers=auth_headers(token))
    if r.status_code != 200:
        log.warning(f'Unable to fetch scenes')
        return
    response = json.loads(r.text)
    if response['count'] != 1:
        log.warning(f'Unable to find scene with name "{name}"')
        return
    scene = response['results'][0]
    endpoint = f"{url}/api/v1/scenes/{scene['id']}/download"
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        log.warning(f"Unable to get download link for scene {scene['id']}")
        return
    response = json.loads(r.text)
    name_slug = f"{scene['name'].replace(' ', '_')}-{scene['id'][:8]}.zip"
    output_path = to_pathlib_path(path) / name_slug
    download_url(response['redirect_link'], output_path)


def fetch_scenes(endpoint, token):
    """ fetch all datasets in ragnarok """
    endpoint = f'{endpoint}/api/v1/scenes/'
    r = requests.get(endpoint, headers=auth_headers(token))
    if r.status_code != 200:
        log.warning('Unable to fetch scenes')
        return
    scenes = json.loads(r.text)['results']
    tbl = TableLogger(columns='state,name,zpy_version,blender_version,created',default_colwidth=30)
    if len(scenes) == 0:
        log.info(None)
    for s in scenes:
        tbl(s['state'], s['name'], s['zpy_version'], s['blender_version'], s['created_at'])
