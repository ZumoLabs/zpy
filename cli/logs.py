from cli.utils import fetch_auth, download_url
from zpy.files import to_pathlib_path
import json
import requests

LOG_TYPES = ["info", "debug", "error"]


@fetch_auth
def fetch_logs(resource, name, path, url, auth_headers):
    """fetch logs

    Fetch LOG_TYPES for a backend run.

    Args:
        type (str): resource to fetch logs
        name (str): name of resource
        path (str): output_dir
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/{resource}/"
    r = requests.get(endpoint, params={"name": name}, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    if response["count"] != 1:
        raise NameError(f"found {response['count']} {resource} for name {name}")
    obj = response["results"][0]
    endpoint = f"{url}/api/v1/{resource}/{obj['id']}/logs"
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    output_dir = to_pathlib_path(path)
    for log_type in LOG_TYPES:
        output_path = output_dir / f"{log_type}.log"
        download_url(response[log_type]["redirect_link"], output_path)
