from requests.auth import HTTPBasicAuth
from zpy.files import to_pathlib_path
import logging
import os
import requests
import yaml

log = logging.getLogger(__name__)

ENDPOINTS = {
    'local': 'http://localhost:8000',
    'stage': 'https://ragnarok.stage.zumok8s.org',
    'prod':  'https://ragnarok.zumok8s.org'
}
CONFIG_FILE = '~/.zpy/config.yaml'


def initialize_config():
    """ Initialize zpy config if missing """
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    if path.exists():
        log.debug(f'found zpy config {path}')
        config = read_config()
        log.debug(config)
        return
    CONFIG = {
        'ENVIRONMENT': 'prod',
        'TOKEN': None,
        'ENDPOINT': ENDPOINTS['prod']
    }
    log.debug(f'initializing new zpy config {path}...')
    path.parent.mkdir(parents=True, exist_ok=True)
    log.debug(CONFIG)
    write_config(CONFIG)
    log.info('please login to fetch token')


def login(username, password):
    config = read_config()
    endpoint = f"{config['ENDPOINT']}/auth/login/"
    log.info(f'login {endpoint}')
    r = requests.post(endpoint, auth=HTTPBasicAuth(username, password))
    if r.status_code != 200:
        log.warning(f'unable to login user {username}')
        return
    token = r.json()['token']
    write_token(token)
    log.warning(f'successful login for user {username}')


def write_token(token):
    config = read_config()
    config['TOKEN'] = token
    write_config(config)


def switch_env(env):
    config = read_config()
    if config['ENVIRONMENT'] == env:
        return
    config['ENVIRONMENT'] = env
    config['ENDPOINT'] = ENDPOINTS[env]
    config['TOKEN'] = None
    write_config(config)
    log.info('please login to fetch token')


def read_config():
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    log.debug(f'Reading zpy config {path}')
    with path.open() as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def write_config(config):
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    log.debug(f'Writing zpy config {path}')
    with path.open('w') as f:
        yaml.dump(config, f)
