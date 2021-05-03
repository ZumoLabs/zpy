from zpy.files import to_pathlib_path
import os
import yaml

ENDPOINTS = {
    "local": "http://localhost:8000",
    "stage": "https://ragnarok.stage.zumok8s.org",
    "prod": "https://ragnarok.zumok8s.org",
}
CONFIG_FILE = "~/.zpy/config.yaml"


def get_endpoint(env):
    """get endpoint

    Given an env return endpoint
    Args:
        env (str): desired env

    Returns:
        url (str): endpoint for env
    """
    return ENDPOINTS[env]


def initialize_config():
    """initialize config

    If CONFIG_FILE doesnt exist write it and put in prod as the endpoint. Also creates
    the ~/.zpy folder if not existing. The config is some variables needed by the cli to
    make validated requests to the backend.
    """
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    if path.exists():
        return
    CONFIG = {"ENVIRONMENT": "prod", "TOKEN": None, "ENDPOINT": ENDPOINTS["prod"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    write_config(CONFIG)


def read_config():
    """read config

    Read zpy cli configuration file.

    Returns:
        config: dictionary of current configuration
    """
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    with path.open() as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def write_config(config):
    """write config

    Write zpy cli configuration file.

    Args:
        config (dict): new configuration to write
    """
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    with path.open("w") as f:
        yaml.dump(config, f)
