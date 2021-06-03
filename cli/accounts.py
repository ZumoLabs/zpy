import json

import requests

from cli.utils import fetch_auth


@fetch_auth
def fetch_accounts(filters, url, auth_headers):
    """fetch accounts

    Fetch accounts from ZumoLabs backend.

    Args:
        filters (dict): query param filters for API call
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/accounts/"
    r = requests.get(endpoint, headers=auth_headers, params=filters)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)["results"]
