"""
    Common utilities for tesseract.

    NOTE: Should only include default python modules.
"""
import csv
import json
import logging
import os
import random
import re
import shutil
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, List, Tuple, Union

log = logging.getLogger(__name__)


'''
Dictionary of filename extensions and prefix/suffixes

These serve as the master search patterns so update and use
these as much as possible to prevent bugs.

Order matters! More specific regexes at the top and
catch-alls at the bottom.

You can test these out at: https://regex101.com/
'''
IMAGE_REGEX = '.*\.(jpeg|jpg|png|bmp)'
ANNOTATION_REGEX = '.*\.(json|xml|yaml)'
FILE_TYPE_REGEX = {
    # Images
    'instance segmentation image': 'IMG_[0-9]*_iseg' + IMAGE_REGEX,
    'class segmentation image': 'IMG_[0-9]*_cseg' + IMAGE_REGEX,
    'depth image': 'IMG_[0-9]*_depth' + IMAGE_REGEX,
    'normal image': 'IMG_[0-9]*_normal' + IMAGE_REGEX,
    'stereo left image': 'IMG_[0-9]*_stereoL' + IMAGE_REGEX,
    'stereo right image': 'IMG_[0-9]*_stereoR' + IMAGE_REGEX,
    'rgb image': 'IMG_[0-9]*_rgb' + IMAGE_REGEX,
    'image': IMAGE_REGEX,
    # Annotations
    'zumo annotation': 'ZUMO_[0-9]*.json',
    'zumo metafile': 'ZUMO_META.json',
    'annotation': ANNOTATION_REGEX,
}


def dataset_contents(
    path: Union[str, Path],
    filetype_regex: Dict = FILE_TYPE_REGEX,
) -> Dict:
    """Use regex to search inside a data directory."""
    path = verify_path(path, check_dir=True, make=False)
    contents = {
        'dirs': [],
    }
    for dirpath, _, files in os.walk(path):
        contents['dirs'].append(dirpath)
        for filename in files:
            for name, re_pattern in filetype_regex.items():
                if re.search(re_pattern, filename):
                    if contents.get(name, None) is None:
                        contents[name] = []
                    contents[name].append(os.path.join(dirpath, filename))
                    break
    return contents


def file_is_of_type(filename: Union[str, Path], filetype: str) -> bool:
    """ Check to see if file is of type given by regex."""
    if isinstance(filename, Path):
        filename = str(filename)
    assert FILE_TYPE_REGEX.get(filetype, None) is not None, \
        f'{filetype} must be in {FILE_TYPE_REGEX.keys()}'
    if re.search(FILE_TYPE_REGEX[filetype], filename):
        return True
    return False


def make_rgb_image_name(idx: int, extension: str = '.png') -> str:
    """ Return rgb image name from image id. """
    return 'IMG_%08d_rgb' % idx + extension


def make_cseg_image_name(idx: int, extension: str = '.png') -> str:
    """ Return class segmentation image name from image id. """
    return 'IMG_%08d_cseg' % idx + extension


def make_iseg_image_name(idx: int, extension: str = '.png') -> str:
    """ Return instance segmentation image name from image id. """
    return 'IMG_%08d_iseg' % idx + extension


def make_depth_image_name(idx: int, extension: str = '.png') -> str:
    """ Return instance segmentation image name from image id. """
    return 'IMG_%08d_depth' % idx + extension


def frame_from_image_name(image_name: str) -> int:
    """ Extract frame id from image name. """
    return int(''.join([s for s in image_name if s.isdigit()]))


def make_underscore_path(path: Union[str, Path], name: str) -> Path:
    """ Make an underscore path: foo.txt -> foo_new.txt """
    path = to_pathlib_path(path)
    underscore_filename = path.stem + '_' + name + path.suffix
    return path.parent / Path(underscore_filename)


def to_pathlib_path(path: Union[str, Path]) -> Path:
    """Convert string path to pathlib.Path if needed."""
    if not isinstance(path, Path):
        path = Path(os.path.expandvars(path))
    return path


def clean_dir(
    path: Union[str, Path],
    keep_dir: bool = True,
) -> None:
    """Delete everything at the provided directory."""
    path = verify_path(path, make=False, check_dir=True)
    if keep_dir:
        # Delete the contents, but keep the directory
        for _path in path.iterdir():
            try:
                if _path.is_file() or _path.is_symlink():
                    _path.unlink()
                elif _path.is_dir():
                    shutil.rmtree(_path)
            except Exception as e:
                log.warning('Failed to delete %s. Reason: %s' % (_path, e))
    else:
        # Delete everything, including the directory itself
        shutil.rmtree(path)


def pretty_print(_d: Dict) -> str:
    """ Pretty print default formatting """
    return pformat(_d, indent=2, width=120)


def verify_path(path: Union[str, Path],
                make: bool = False,
                check_dir: bool = False,
                ) -> Path:
    """Verifies (or creates) directory at path."""
    path = to_pathlib_path(path)
    if not path.exists():
        log.warning(f'Could not find path at {path}')
        if make:
            log.info(f'Making {path.name} dir at {path}')
            path.mkdir(exist_ok=True, parents=True)
    else:
        log.debug(f'Path found at {path}.')
        if check_dir and not path.is_dir():
            raise ValueError(f'Path at {path} is not a directory.')
    return path


def write_json(path: Union[str, Path], data: Union[Dict, List]) -> None:
    """ Save data to path """
    path = to_pathlib_path(path)
    log.info(f'Writing JSON to file {path}')
    with path.open('w') as f:
        json.dump(data, f, indent=4)


def read_json(path: Union[str, Path]) -> Union[Dict, List]:
    """ Read data from path """
    path = to_pathlib_path(path)
    log.info(f'Reading JSON file at {path}')
    with path.open() as f:
        data = json.load(f)
    return data


def write_csv(
    path: Union[str, Path],
    data: List[List[Any]],
    delimiter: str = ',',
    **kwargs
) -> None:
    """ Save data to path """
    path = to_pathlib_path(path)
    log.info(f'Writing CSV to file {path}')
    with path.open('w') as f:
        writer = csv.writer(f, delimiter=delimiter, **kwargs)
        writer.writerows(data)


def read_csv(
    path: Union[str, Path],
    delimiter: str = ',',
    **kwargs
) -> List[List[Any]]:
    """ Read data from path """
    path = to_pathlib_path(path)
    log.info(f'Reading CSV file at {path}')
    data = []
    with path.open() as f:
        for row in csv.reader(f, delimiter=delimiter, **kwargs):
            data.append(row)
    return data


def sample(things: List, sample_size: int = None) -> List:
    """ Return a sample of things. """
    random_sample_size = len(things)
    if sample_size is not None:
        random_sample_size = min(sample_size, len(things))
    if random_sample_size == len(things):
        sample_images = things
    else:
        sample_images = random.sample(things, random_sample_size)
    return sample_images


def filecopy(src_dir: Union[str, Path] = None,
             dst_dir: Union[str, Path] = None,
             src_name: str = None,
             dst_name: str = None):
    """ Copy over a file. """
    src_dir = verify_path(src_dir, check_dir=True)
    dst_dir = verify_path(dst_dir, check_dir=True)
    src = src_dir / src_name
    dst = dst_dir / dst_name
    src = verify_path(src)
    dst = verify_path(dst)
    log.debug(f'Copying over file from {src} to {dst}')
    shutil.copy(src, dst)
