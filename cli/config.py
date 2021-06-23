from zpy.files import to_pathlib_path
import os
import yaml

ENDPOINT = "https://ragnarok.zumok8s.org"
CONFIG_FILE = "~/.zpy/config.yaml"


def initialize_config():
    """initialize config

    If CONFIG_FILE doesnt exist write it and put in prod as the endpoint. Also creates
    the ~/.zpy folder if not existing. The config is some variables needed by the cli to
    make validated requests to the backend.
    """
    path = to_pathlib_path(os.path.expanduser(CONFIG_FILE))
    if path.exists():
        return
    CONFIG = {"ENVIRONMENT": "prod", "TOKEN": None, "ENDPOINT": ENDPOINT}
    path.parent.mkdir(parents=True, exist_ok=True)
    write_config(CONFIG)


def read_config(file=CONFIG_FILE):
    """read config

    Read zpy cli configuration file.

    Args:
        env: which enviroment to read config for
    Returns:
        config: dictionary of current configuration
    """
    path = to_pathlib_path(os.path.expanduser(file))
    with path.open() as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def write_config(config, file=CONFIG_FILE):
    """write config

    Write zpy cli configuration file.

    Args:
        config (dict): new configuration to write
    """
    path = to_pathlib_path(os.path.expanduser(file))
    with path.open("w") as f:
        yaml.dump(config, f)


def add_env(name, endpoint):
    """add environment

    Add a new environment configuration file.

    Args:
        name: name of the environment
        endpoint: endpoint for the new enviroment
    """
    new_config = {"ENVIRONMENT": name, "TOKEN": None, "ENDPOINT": endpoint}
    write_config(new_config, file=f"~/.zpy/{name}.yaml")


def swap_env(name):
    """swap environment

    Swap the current environment configuration.

    Args:
        name: swap to this env
    """
    old_config = read_config()
    new_config = read_config(file=f"~/.zpy/{name}.yaml")
    write_config(new_config)
    write_config(old_config, file=f"~/.zpy/{old_config['ENVIRONMENT']}.yaml")
