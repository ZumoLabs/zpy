from cli.utils import fetch_auth, download_url
from zpy.files import to_pathlib_path
import json
import requests


@fetch_auth
def fetch_sim(name, url, auth_headers):
    """fetch sim

    Fetch info on a sim by name from backend.

    Args:
        name (str): name of sim
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/sims/"
    r = requests.get(endpoint, params={"name": name}, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    if response["count"] != 1:
        raise NameError(f"found {response['count']} sims for name {name}")
    return response["results"][0]


@fetch_auth
def create_sim(name, path, project, url, auth_headers):
    """create sim

    Upload sim object to S3 through ZumoLabs backend and create
    the sim object.

    Args:
        project (str): uuid of parent project
        name (str): name of sim to upload
        path (str): file to upload
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/sims/"
    r = requests.post(
        endpoint,
        data={"name": name, "project": project},
        files={"file": open(path, "rb")},
        headers=auth_headers,
    )
    if r.status_code != 201:
        r.raise_for_status()


@fetch_auth
def download_sim(name, path, url, auth_headers):
    """download sim

    Download sim object from S3 through ZumoLabs backend.

    Args:
        name (str): name of sim to download
        path (str): output directory
        url (str): backend endpoint
        auth_headers: authentication for backend

    Returns:
        str: output file path
    """
    sim = fetch_sim(name)
    endpoint = f"{url}/api/v1/sims/{sim['id']}/download"
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    name_slug = f"{sim['name'].replace(' ', '_')}-{sim['id'][:8]}.zip"
    output_path = to_pathlib_path(path) / name_slug
    download_url(response["redirect_link"], output_path)
    return output_path


@fetch_auth
def fetch_sims(filters, url, auth_headers):
    """fetch sims

    Fetch sim objects from ZumoLabs backend.

    Args:
        filters (dict): query param filters for API call
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/sims/"
    r = requests.get(endpoint, headers=auth_headers, params=filters)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)["results"]
