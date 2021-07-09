from cli.utils import fetch_auth
import requests
import json


@fetch_auth
def create_new_job(name, operation, config, datasets, project, url, auth_headers):
    """create job

    Create a job object on ZumoLabs backend. This will trigger the backend
    to run the job.

    Args:
        name (str): name of job
        operation (str): job type
        config (dict): configuration for job
        datasets (dict): list of dataset ids
        url (str): backend endpoint
        auth_headers: authentication for backend
        project (str): project uuid
    """
    endpoint = f"{url}/api/v1/jobs/"
    data = {
        "project": project,
        "operation": operation.upper(),
        "name": name,
        "input_datasets": datasets,
        "config": json.dumps(config),
    }
    r = requests.post(endpoint, data=data, headers=auth_headers)
    if r.status_code != 201:
        r.raise_for_status()


@fetch_auth
def fetch_jobs(filters, url, auth_headers):
    """fetch jobs

    Fetch job objects from ZumoLabs backend.

    Args:
        filters (dict): query param filters for API call
        url (str): backend endpoint
        auth_headers: authentication for backend

    Returns:
        list: list of jobs
    """
    endpoint = f"{url}/api/v1/jobs/"
    r = requests.get(endpoint, headers=auth_headers, params=filters)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)["results"]
