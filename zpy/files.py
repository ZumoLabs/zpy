"""
    File utilities.
"""
import csv
import json
import logging
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, List, Union

log = logging.getLogger(__name__)


"""
Dictionary of filename extensions and prefix/suffixes

These serve as the master search patterns so update and use
these as much as possible to prevent bugs.

Order matters! More specific regexes at the top and
catch-alls at the bottom.

You can test these out at: https://regex101.com/
"""
IMAGE_REGEX = ".*\.(jpeg|jpg|png|bmp)"
FILE_REGEX = {
    # Images
    "instance segmentation image": ".*iseg" + IMAGE_REGEX,
    "class segmentation image": ".*cseg" + IMAGE_REGEX,
    "depth image": ".*depth" + IMAGE_REGEX,
    "normal image": ".*normal" + IMAGE_REGEX,
    "stereo left image": ".*.stereoL" + IMAGE_REGEX,
    "stereo right image": ".*.stereoR" + IMAGE_REGEX,
    "rgb image": ".*rgb" + IMAGE_REGEX,
    "image": IMAGE_REGEX,
    # Annotations
    "zumo annotation": "_annotations.zumo.json",
    "coco annotation": ".*coco.*\.json",
    "annotation": ".*\.(json|xml|yaml|csv)",
}


def dataset_contents(
    path: Union[Path, str],
    filetype_regex: Dict = FILE_REGEX,
) -> Dict:
    """Use regex to search inside a data directory.

    Args:
        path (Union[Path, str]): Directory filepath.
        filetype_regex (Dict, optional): dictionary of {filetype : regex}

    Returns:
        Dict: Contents of directory.
    """
    path = verify_path(path, check_dir=True, make=False)
    contents = {
        "dirs": [],
    }
    for dirpath, _, files in os.walk(path):
        contents["dirs"].append(dirpath)
        for filename in files:
            for name, re_pattern in filetype_regex.items():
                if re.search(re_pattern, filename):
                    if contents.get(name, None) is None:
                        contents[name] = []
                    contents[name].append(os.path.join(dirpath, filename))
                    break
    return contents


def file_is_of_type(
    path: Union[Path, str],
    filetype: str,
) -> bool:
    """Check to if file is of type given.

    Args:
        path (Union[Path, str]): A filesystem path.
        filetype (str): Type of file (see FILE_REGEX dict in zpy.files)

    Returns:
        bool: File is that type.
    """
    if isinstance(path, Path):
        path = str(path)
    assert (
        FILE_REGEX.get(filetype, None) is not None
    ), f"{filetype} must be in {FILE_REGEX.keys()}"
    if re.search(FILE_REGEX[filetype], path):
        return True
    return False


def make_rgb_image_name(id: int, extension: str = ".png") -> str:
    """Creates a RGB image name given an integer id.

    Args:
        id (int): Integer id used in name creation.
        extension (str, optional): Extension for image. Defaults to '.png'.

    Returns:
        str: Image name.
    """
    return "image.%06d.rgb" % id + extension


def make_cseg_image_name(id: int, extension: str = ".png") -> str:
    """Return category (class) segmentation image name from integer id.

    Args:
        id (int): Integer id used in name creation.
        extension (str, optional): Extension for image. Defaults to '.png'.

    Returns:
        str: Image name.
    """
    return "image.%06d.cseg" % id + extension


def make_iseg_image_name(id: int, extension: str = ".png") -> str:
    """Return instance segmentation image name from integer id.

    Args:
        id (int): Integer id used in name creation.
        extension (str, optional): Extension for image. Defaults to '.png'.

    Returns:
        str: Image name.
    """
    return "image.%06d.iseg" % id + extension


def make_depth_image_name(id: int, extension: str = ".png") -> str:
    """Return depth image name from integer id.

    Args:
        id (int): Integer id used in name creation.
        extension (str, optional): Extension for image. Defaults to '.png'.

    Returns:
        str: Image name.
    """
    return "image.%06d.depth" % id + extension


def make_custom_image_name(id: int, name: str, extension: str = ".png") -> str:
    """Creates a custom image name given integer id and name.

    Args:
        id (int): Integer id used in name creation.
        name (str): Custom string which will be appended to the end of the image name.
        extension (str, optional): Extension for image. Defaults to '.png'.

    Returns:
        str: Image name.
    """
    return "image.%06d.%s" % (id, name) + extension


def id_from_image_name(image_name: str) -> int:
    """Extract integer id from image name.

    Args:
        image_name (str): Name of image to extract integer from.

    Returns:
        int: Integer id.
    """
    return int("".join([s for s in image_name if s.isdigit()]))


def replace_id_in_image_name(image_name: str, new_id: int) -> str:
    """Replace the integer id in an image name.

    Args:
        image_name (str): Name of the image.
        new_id (int): New id to replace old id with.

    Returns:
        str: New image name.
    """
    # HACK: This will break for image names without 8-digit indices
    return "image.%06d" % new_id + image_name[12:]


def add_to_path(path: Union[Path, str], name: str) -> Path:
    """Add string descriptor to path: foo.txt -> foo.more_foo.txt

    Args:
        path (Union[Path, str]): A filesystem path.
        name (str): Name to append to file name.

    Returns:
        Path: New path.
    """
    path = to_pathlib_path(path)
    underscore_filename = path.stem + "_" + name + path.suffix
    return path.parent / Path(underscore_filename)


def to_pathlib_path(path: Union[Path, str]) -> Path:
    """Convert string path to pathlib.Path if needed.

    Args:
        path (Union[Path, str]): A filesystem path.

    Returns:
        Path: Path in pathlib.Path format.
    """
    if not isinstance(path, Path):
        path = Path(os.path.expandvars(path)).resolve()
    return path


def default_temp_path() -> Path:
    """Default temporary path agnostic to OS.

    Returns:
        Path: Path to a new output folder in the temp path.
    """
    return Path(tempfile.gettempdir()) / "output"


def clean_dir(
    path: Union[Path, str],
    keep_dir: bool = True,
) -> None:
    """Delete everything at the provided directory.

    Args:
        path (Union[Path, str]): Path to directory.
        keep_dir (bool, optional): Whether to keep (or delete) the directory itself. Defaults to True.
    """
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
                log.warning("Failed to delete %s. Reason: %s" % (_path, e))
    else:
        # Delete everything, including the directory itself
        shutil.rmtree(path)


def pretty_print(d: Dict) -> str:
    """Pretty formatted dictionary.

    Args:
        d (Dict): Dictionary to be pretty printed

    Returns:
        str: Dictionary in pretty format.
    """
    return pformat(d, indent=2, width=120)


def verify_path(
    path: Union[Path, str],
    make: bool = False,
    check_dir: bool = False,
) -> Path:
    """Checks to make sure Path exists and optionally creates it.

    Args:
        path (Union[Path, str]): A filesystem path.
        make (bool, optional): Make the path if it does not exist. Defaults to False.
        check_dir (bool, optional): Throw error is path is not a directory. Defaults to False.

    Raises:
        ValueError: Path is not a directory (only if check_dir is set to True)

    Returns:
        Path: The same path.
    """
    path = to_pathlib_path(path)
    if not path.exists():
        log.warning(f"Could not find path at {path}")
        if make:
            log.info(f"Making {path.name} dir at {path}")
            path.mkdir(exist_ok=True, parents=True)
    else:
        log.debug(f"Path found at {path}.")
        if check_dir and not path.is_dir():
            raise ValueError(f"Path at {path} is not a directory.")
    return path


def write_json(
    path: Union[Path, str],
    data: Union[Dict, List],
) -> None:
    """Save data to json file.

    Args:
        path (Union[Path, str]): Path to output json.
        data (Union[Dict, List]): Data to save.

    Raises:
        ValueError: Path is not a json file.
    """
    path = to_pathlib_path(path)
    if not path.suffix == ".json":
        raise ValueError(f"{path} is not a JSON file.")
    log.info(f"Writing JSON to file {path}")
    with path.open("w") as f:
        json.dump(data, f, indent=4)


def read_json(
    path: Union[Path, str],
) -> Union[Dict, List]:
    """Read a json from a path.

    Args:
        path (Union[Path, str]): A filesystem path.

    Raises:
        ValueError: Path is not a json file.

    Returns:
        Union[Dict, List]: Data in the json.
    """
    path = to_pathlib_path(path)
    if not path.suffix == ".json":
        raise ValueError(f"{path} is not a JSON file.")
    log.info(f"Reading JSON file at {path}")
    with path.open() as f:
        data = json.load(f)
    return data


def write_csv(
    path: Union[Path, str], data: List[List[Any]], delimiter: str = ",", **kwargs
) -> None:
    """Write data to csv.

    Pass in additional kwargs to the csv writer.

    Args:
        path (Union[Path, str]): A filesystem path.
        data (List[List[Any]]): Data to save.
        delimiter (str, optional): Delimiter for each row of csv. Defaults to ','.

    Raises:
        ValueError: Path is not a csv or txt file.
    """
    path = to_pathlib_path(path)
    if path.suffix not in [".csv", ".txt"]:
        raise ValueError(f"{path} is not a CSV file.")
    log.info(f"Writing CSV to file {path}")
    with path.open("w") as f:
        writer = csv.writer(f, delimiter=delimiter, **kwargs)
        writer.writerows(data)


def read_csv(path: Union[Path, str], delimiter: str = ",", **kwargs) -> List[List[Any]]:
    """Read csv data from a path.

    Pass in additional kwargs to the csv reader.

    Args:
        path (Union[Path, str]): A filesystem path.
        delimiter (str, optional): Delimiter for each row of csv. Defaults to ','.

    Raises:
        ValueError: Path is not a csv or txt file.

    Returns:
        List[List[Any]]: Data in the csv.
    """
    path = to_pathlib_path(path)
    if path.suffix not in [".csv", ".txt"]:
        raise ValueError(f"{path} is not a CSV file.")
    log.info(f"Reading CSV file at {path}")
    data = []
    with path.open() as f:
        for row in csv.reader(f, delimiter=delimiter, **kwargs):
            data.append(row)
    return data


def pick_random_from_dir(
    dir_path: Union[Path, str],
    suffixes: List[str] = [".txt"],
) -> Path:
    """Pick random file of suffix in a directory.

    Args:
        dir_path (Union[Path, str]): Path to the directory containing files.
        suffixes (List[str], optional): Filter files by these suffixes. Defaults to [].

    Returns:
        Path: Path to randomly chosen file with given suffix.
    """
    _paths = []
    for _path in dir_path.iterdir():
        if _path.is_file() and _path.suffix in suffixes:
            _paths.append(_path)
    _path = random.choice(_paths)
    log.debug(f"Found {len(_paths)} files with suffix {suffixes} at {dir_path}")
    log.info(f"Randomly chose {_path}")
    return _path


def sample(
    things: List,
    sample_size: int = None,
) -> List:
    """Sample N things from a list.

    Args:
        things (List): List of things.
        sample_size (int, optional): Sample size N. Defaults to length of things.

    Returns:
        List: New sample of things.
    """
    random_sample_size = len(things)
    if sample_size is not None:
        random_sample_size = min(sample_size, len(things))
    if random_sample_size == len(things):
        sample_images = things
    else:
        sample_images = random.sample(things, random_sample_size)
    return sample_images


def filecopy(
    src_path: Union[Path, str],
    dst_path: Union[Path, str],
) -> None:
    """Copy file from source (src) to destination (dst).

    Args:
        src_path (Union[Path, str]): Source filesystem path.
        dst_path (Union[Path, str]): Destination filesystem path.
    """
    src_path = verify_path(src_path)
    dst_path = verify_path(dst_path)
    log.debug(f"Copying over file from {src_path} to {dst_path}")
    shutil.copy(src_path, dst_path)


def open_folder_in_explorer(
    path: Union[Path, str],
    make: bool = False,
) -> None:
    """Opens a directory in the fileexplorer of your OS.

    Args:
        path (Union[Path, str]): Filesystem path.
        make (bool, optional): Make directory if it doesn't exist. Defaults to False.
    """
    path = verify_path(path, check_dir=True, make=make)
    if sys.platform.startswith("darwin"):
        subprocess.call(("open", path))
    elif os.name == "nt":
        os.startfile(path)
    elif os.name == "posix":
        subprocess.call(("xdg-open", path))


def remove_files_with_suffix(
    path: Union[Path, str],
    exts: List[str],
) -> None:
    """Remove file in a path with certain extension.

    Args:
        path (Union[Path, str]): Directory path.
        exts (List[str]): List of extensions to remove
    """
    path = verify_path(path, check_dir=True)
    for _path in path.glob("*"):
        if _path.suffix in exts:
            log.info(f"Removing file at {_path}")
            _path.unlink()


def unzip_file(
    zip_path: Union[Path, str],
    out_path: Union[Path, str],
) -> None:
    """Unzip a file to an output path.

    Args:
        zip_path (Union[Path, str]): Path to zip file.
        out_path (Union[Path, str]): Path to output directory.

    Raises:
        ValueError: Path isn't a zip.
    """
    log.info(f"Unzipping {zip_path} to {out_path}...")
    zip_path = verify_path(zip_path)
    out_path = verify_path(out_path, check_dir=True)
    if not zip_path.suffix == ".zip":
        raise ValueError(f"{zip_path} is not a zip file")
    zf = zipfile.ZipFile(str(zip_path))
    zipped_size_mb = round(sum([i.compress_size for i in zf.infolist()]) / 1024 / 1024)
    unzipped_size_mb = round(sum([i.file_size for i in zf.infolist()]) / 1024 / 1024)
    log.info(f"Compressed: {zipped_size_mb}MB, actual: {unzipped_size_mb}MB.")
    zf.extractall(out_path)
    log.info(f"Done extracting to {out_path}.")


def zip_file(
    in_path: Union[Path, str],
    zip_path: Union[Path, str],
) -> None:
    """Zip a directory to a path.

    Args:
        in_path (Union[Path, str]): Path to input directory.
        zip_path (Union[Path, str]): Path to zip file.

    Raises:
        ValueError: Path isn't a zip.
    """
    log.info(f"Zipping {in_path} to {zip_path}...")
    in_path = verify_path(in_path)
    zip_path = verify_path(zip_path)
    if not zip_path.suffix == ".zip":
        raise ValueError(f"{zip_path} is not a zip file")
    shutil.make_archive(
        base_name=zip_path.parent / zip_path.stem, format="zip", root_dir=in_path
    )
    log.info(f"Done zipping to {zip_path}.")
    zf = zipfile.ZipFile(str(zip_path))
    zipped_size_mb = round(sum([i.compress_size for i in zf.infolist()]) / 1024 / 1024)
    unzipped_size_mb = round(sum([i.file_size for i in zf.infolist()]) / 1024 / 1024)
    log.info(f"Compressed: {zipped_size_mb}MB, actual: {unzipped_size_mb}MB.")
