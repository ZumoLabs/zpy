from pathlib import Path
from tqdm import tqdm
from typing import Union
from urllib.parse import urlparse
from urllib.request import urlopen
from cli.config import read_config
import functools
import logging
import os
import random

log = logging.getLogger(__name__)


def parse_dataset_filter(dfilter):
    """ parse a dataset filter string """
    dfilter_arr = dfilter.split(':')
    field, pattern, regex = 'name', 'startswith', dfilter_arr[-1]
    if len(dfilter_arr) == 2:
        pattern = dfilter_arr[0]
    elif len(dfilter_arr) == 3:
        field, pattern = dfilter_arr[0], dfilter_arr[1]
    return field, pattern, regex


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


def fetch_auth(func):
    """ Decorator to fetch info for cli from config

    Args:
        func: function to wrap

    Returns:
        wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        config = read_config()
        endpoint = config['ENDPOINT']
        auth_header = auth_headers(config['TOKEN'])
        return func(*args, **kwargs, url=endpoint, auth_headers=auth_header)
    return wrapper
