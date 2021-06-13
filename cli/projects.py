import json

import requests

from cli.utils import fetch_auth


@fetch_auth
def fetch_projects(filters, url, auth_headers):
    """fetch projects

    Fetch projects from ZumoLabs backend.

    Args:
        filters (dict): query param filters for API call
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/projects/"
    r = requests.get(endpoint, headers=auth_headers, params=filters)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)["results"]


@fetch_auth
def create_project(account_id, name, url, auth_headers):
    """
    create project

    Create empty project on ZumoLabs backend.

    Args:
        account_id (str): uuid of account
        name (str): name of project
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/projects/"
    r = requests.post(
        endpoint,
        data={"account": account_id, "name": name},
        headers=auth_headers,
    )
    if r.status_code != 201:
        r.raise_for_status()
