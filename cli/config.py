from zpy.files import to_pathlib_path
import os
import yaml

ENDPOINTS = {
    'local': 'http://localhost:8000',
    'stage': 'https://ragnarok.stage.zumok8s.org',
    'prod':  'https://ragnarok.zumok8s.org'
}
CONFIG_FILE = '~/.zpy/config.yaml'


def initialize_config():
    """ Initialize zpy config file if missing """
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    if path.exists():
        config = read_config()
        return
    CONFIG = {
        'ENVIRONMENT': 'prod',
        'TOKEN': None,
        'ENDPOINT': ENDPOINTS['prod']
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    write_config(CONFIG)


def read_config():
    """ read zpy configuration file """
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    with path.open() as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def write_config(config):
    """ write zpy configuration file """
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    with path.open('w') as f:
        yaml.dump(config, f)
