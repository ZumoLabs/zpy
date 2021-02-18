from pathlib import Path
from typing import Union
import os
from tqdm import tqdm
from urllib.request import urlopen
from urllib.parse import urlparse
import logging
import random

log = logging.getLogger(__name__)


def _safe_eval(key):
    try:
        return eval(key)
    except:
        return key


def parse_args(args):
    keys = args[::2]
    vals = map(lambda x: _safe_eval(x), args[1::2])
    return dict(zip(keys,vals))


def download_url(url, output_path):
    u = urlopen(url)
    h = u.info()
    totalSize = int(h["Content-Length"])

    log.info(f"Downloading {totalSize} bytes...")
    fp = open(output_path, 'wb')

    blockSize = 8192
    with tqdm(total=totalSize) as pbar:
        while True:
            chunk = u.read(blockSize)
            if not chunk: 
                break
            fp.write(chunk)
            pbar.update(blockSize)

    fp.flush()
    fp.close()

    log.info('Downloaded:')
    log.info(f'url: {url}')
    log.info(f'local path: {output_path}')


def auth_headers(token):
    return {'Authorization': 'token {}'.format(token)}


def to_pathlib_path(path: Union[str, Path]) -> Path:
    """ Convert string path to pathlib.Path if needed. """
    if not isinstance(path, Path):
        path = Path(os.path.expandvars(path))
    return path
