import functools
import math
import sys

import requests
from requests import HTTPError


def add_newline(func):
    """Decorator to print a new line after the function call.

    Args:
        func: function to wrap

    Returns:
        wrapped function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        print("\n")
        return ret

    return wrapper


def auth_header(auth_token):
    return {"Authorization": f"Token {auth_token}"}


def handle_response(response: requests.Response):
    """Shared logic for handling API responses.

    Args:
        response: Request to handle
    Returns:
        deserialized json response
    """
    if response.status_code != 200:
        if response.status_code == 400:
            # Known error from the server will have a nice message.
            raise HTTPError(response.json())
        else:
            response.raise_for_status()

    return response.json()


def get(url, **kwargs):
    """GET a url. Forwards kwargs to requests.get
    TODO: Merge with calling code in zpy/cli/

    Args:
        url (str): Ragnarok API url
        kwargs: Forwarded to the requests.get function call
    Returns:
        deserialized API response
    Raises:
        HTTPError
    """
    verbose = kwargs.pop("verbose", False)
    response = requests.get(url, **kwargs)
    if verbose:
        print(response.url)
    return handle_response(response)


def post(url, **kwargs):
    """POST to a url. Forwards kwargs to requests.post
    TODO: Merge with calling code in zpy/cli/

    Args:
        url (str): Ragnarok API url
        kwargs: Forwarded to the requests.post function call
    Returns:
        deserialized API response
    Raises:
        HTTPError
    """
    return handle_response(requests.post(url, **kwargs))


def to_query_param_value(config):
    """Create the special query parameter value string for filtering generated-data-sets via config values.

    Args:
        config (dict): A dict of gin config values pre-flattened by using django field traversal notation. See Dataset._config
    Returns:
        string value for the config url query parameter
    """
    query_param_values = []
    for django_field_traversal, django_field_value in config.items():
        # Ignore fields set as None. They weren't specifically set or asked for.
        if django_field_value is not None:
            query_param_values.append(f"{django_field_traversal}:{django_field_value}")
    return ",".join(query_param_values)


def remove_none_values(obj: dict):
    """Recreates a dictionary from obj by omitting all key/value pairs where value is None."""
    return {k: v for k, v in obj.items() if v is not None}


def convert_size(size_bytes: int):
    """Converts a number of bytes into a pretty string."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


ERASE_LINE = "\x1b[2K"


def clear_last_print():
    sys.stdout.write(ERASE_LINE)


def is_done(state: str):
    """Returns True if state is a done state, false otherwise."""
    return state in ["READY", "CANCELLED", "PACKAGING_FAILED", "GENERATING_FAILED"]
