import functools
import math
from copy import deepcopy
from itertools import product
from urllib.request import urlopen

import click
from tqdm import tqdm

from cli.config import read_config


def parse_filter(str_filter):
    """parse filter

    Parse filter string to field, pattern, regex.
    Valid patterns depend on field but can include exact, startswith, contains,
    iexact, istartswith, icontains. If no pattern or field is provided the defaults
    are name for field and startswith for pattern.

    Examples:
        icontains:hello
        name:icontains:foobar
        state:iexact:ready
        foo

    Args:
        filter (str): filter query

    Return:
        field: field to filter on
        pattern: pattern to apply regex
        regex: string regex for pattern
    """
    filter_arr = str_filter.split(":")
    field, pattern, regex = "name", "startswith", filter_arr[-1]
    if len(filter_arr) == 2:
        pattern = filter_arr[0]
    elif len(filter_arr) == 3:
        field, pattern = filter_arr[0], filter_arr[1]
    return field, pattern, regex


def resolve_sweep(sweep_config):
    """resolve sweep

    Resolve a dictionary into a sweep of dictionaries. Gin bindings
    are used to communicate with job code and therefore the sweep is done
    across gin_bindings in the sweep_config.

    Example:
        {'foo': ['a', 'b']} -> {'foo': 'a'} {'foo': 'b'}

    Args:
        sweep_config (dict): dictionary to unfold into sweep

    Returns:
        list: list of configs resolved from sweep config
    """
    configs, bindings = [], sweep_config["gin_bindings"]
    for random_binding in [dict(zip(bindings, v)) for v in product(*bindings.values())]:
        config = deepcopy(sweep_config)
        config["gin_bindings"] = random_binding
        configs.append(config)
    return configs


def parse_args(args):
    """parse args

    Used by cli to parse arguments passed to cli calls. Includes
    safe eval function to convert from string to other types.

    Example:
        foo 1 bar 2 -> {'foo': 1, 'bar': 2}
    """

    def _safe_eval(key):
        try:
            return eval(key)
        except Exception:
            return key

    keys = args[::2]
    vals = map(lambda x: _safe_eval(x), args[1::2])
    return dict(zip(keys, vals))


def download_url(url, output_path):
    """download url

    Download from url to give output path and visualize using tqdm.

    Args:
        url (str): url to download
        output_path (str): path to download file to
    """
    u = urlopen(url)
    h = u.info()
    totalSize = int(h["Content-Length"])

    fp = open(output_path, "wb")

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


def fetch_auth(func):
    """fetch authentication

    Decorator to wrap functions providing the backend url and the
    correct authorization headers for requests.

    Args:
        func: function to wrap

    Returns:
        wrapped function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        config = read_config()
        endpoint = config["ENDPOINT"]

        auth_header = {"Authorization": "token {}".format(config["TOKEN"])}
        return func(*args, **kwargs, url=endpoint, auth_headers=auth_header)

    return wrapper


def use_project(required=False):
    def use_project_inner(func):
        """Inject project uuid into function call. Optionally throw an error if it has not been set.

        Args:
            func: function to wrap

        Returns:
            wrapped function
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            config = read_config()
            project = config.get("PROJECT", None)
            if project:
                click.echo(f"Using project {project}")
                return func(*args, **kwargs, project=project)
            else:
                if required:
                    click.secho(
                        "Project is not set. See `zpy project --help`",
                        fg="red",
                        err=True,
                    )
                    return

                return func(*args, **kwargs)

        return wrapper

    return use_project_inner


def print_list_as_columns(list_of_strings, num_cols=5, indent_prefix="    "):
    """Format and echo a list of strings into nicely formatted columns.

    Args:
        list_of_strings (list of str): A list of similar strings to format into columns.
        num_cols (int): Desired number of columns.
        indent_prefix (str): String to attach to the beginning of every printed line.
    Returns:
        None
    """
    count = len(list_of_strings)
    col_width = max(len(string) for string in list_of_strings)
    num_rows = math.ceil(count / num_cols)
    for i in range(num_rows):
        start_index = i * num_cols
        end_index = (i + 1) * num_cols
        if end_index > len(list_of_strings):
            end_index = len(list_of_strings)
        row = list_of_strings[start_index:end_index]

        format_string = indent_prefix + " ".join(
            ["{{:<{}}}".format(col_width) for _ in row]
        )

        click.echo(format_string.format(*row))
