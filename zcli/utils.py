from pathlib import Path
from typing import Union
import os
from tqdm import tqdm
from urllib.request import urlopen
from urllib.parse import urlparse
import logging

log = logging.getLogger(__name__)


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


#def download_url(url, output_dir):
#    parsed_url = urlparse(url)    
#    output_path = to_pathlib_path(output_dir) / os.path.basename(parsed_url.path)
#    with DownloadProgressBar(unit='B', unit_scale=True,
#                             miniters=1, desc=url.split('/')[-1]) as t:
#        #urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)
#        urllib.request.urlretrieve(url)

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
