from pathlib import Path
from typing import Union
import os

def auth_headers(token):
    return {'Authorization': 'token {}'.format(token)}

def to_pathlib_path(path: Union[str, Path]) -> Path:
    """ Convert string path to pathlib.Path if needed. """
    if not isinstance(path, Path):
        path = Path(os.path.expandvars(path))
    return path
