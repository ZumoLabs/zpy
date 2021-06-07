import json

import click
import requests
from requests.auth import HTTPBasicAuth
from table_logger import TableLogger

from cli.config import initialize_config, read_config, write_config, get_endpoint
from cli.loader import Loader
from cli.utils import parse_args, resolve_sweep, use_project, print_list_as_columns
from zpy.files import read_json, to_pathlib_path

SMALL_WIDTH = 12
MEDIUM_WIDTH = 24
LARGE_WIDTH = 36
UUID_WIDTH = 36
DATETIME_WIDTH = 27


@click.group(context_settings=dict(token_normalize_func=str.lower))
def cli():
    """zpy cli

    Zumo Labs cli which is used to create, get, list, upload objects from
    the Zumo Labs backend (ragnarok).
    """
    initialize_config()


@cli.command("help")
def cli_help():
    """display help

    This will display help in order to provide users with more information
    on how to use this tool.
    """
    # TODO: spec this out
    click.echo(
        "zpy - ZumoLabs command line interface\n"
        "\n"
        "zpy is a tool used to list, create, upload, download\n"
        "objects from the ZumoLabs backend (ragnarok)\n"
        "\n"
        "app    - https://app.zumolabs.ai\n"
        "github - https://github.com/ZumoLabs/zpy\n"
        "docs   - https://github.com/ZumoLabs/zpy/tree/main/docs/cli"
    )


@cli.command("env")
@click.argument("env", type=click.Choice(["local", "stage", "prod"]))
def set_env(env):
    """switch target environment

    This command allows zumo labs developers to swap the endpoint that the
    cli communicates with. Unlikely to be relevant for non-zumo devs.

    Args:
        env (str): new environment for endpoint
    """
    config = read_config()
    old_env, old_endpoint = config["ENVIRONMENT"], config["ENDPOINT"]
    config["ENVIRONMENT"] = env
    config["ENDPOINT"] = get_endpoint(env)
    config["TOKEN"] = None
    write_config(config)
    click.echo("Swapped environment:")
    click.echo(f"  {old_env} -> {config['ENVIRONMENT']}")
    click.echo(f"  {old_endpoint} -> {config['ENDPOINT']}")
    click.echo("zpy login to fetch token")


@cli.group("project")
def cli_project():
    """Manage global project workspace."""
    pass


@cli_project.command("set")
@click.argument("project_uuid", type=click.UUID)
def set_project(project_uuid):
    """Set global PROJECT uuid."""
    config = read_config()
    old_project_uuid = config.get("PROJECT", None)
    config["PROJECT"] = str(project_uuid)
    write_config(config)
    click.echo("Switched project:")
    click.echo(f"  {old_project_uuid} -> {config['PROJECT']}")


@cli_project.command("clear")
def clear_project():
    """Clear global PROJECT uuid."""
    config = read_config()
    config.pop("PROJECT")
    write_config(config)
    click.echo("Cleared global project namespace.")


@cli.command("login")
@click.argument("username", required=True)
@click.password_option(help="The login password.")
def login(username, password):
    """login to ragnarok

    This command will update the zpy config with a token that is fetched
    from the backend using account details.

    Accounts can be created at: app.zumolabs.ai

    Args:
        username (str): developer username
        password (str): developer password
    """
    config = read_config()
    endpoint = f"{config['ENDPOINT']}/auth/login/"
    r = requests.post(endpoint, auth=HTTPBasicAuth(username, password))
    if r.status_code != 200:
        click.secho("Login failed.", err=True, fg="red")
        return
    config["TOKEN"] = r.json()["token"]
    write_config(config)
    click.echo("Login successful!")


@cli.command("config")
def cli_config():
    """display config

    Display current configuration file to developer.
    """
    pretty_config = json.dumps(read_config(), indent=2)
    click.echo(f"Zpy cli configuration:\n{pretty_config}")


@cli.command("version")
def version():
    """version

    Display the zpy cli version.
    """
    import zpy

    click.echo(f"Version: {zpy.__version__}")


# ------- LIST


@cli.group("list")
def cli_list():
    """List objects.

    List group is used for list commands on backend objects.
    """
    pass


@cli_list.command("datasets")
@click.argument("filters", nargs=-1)
@use_project()
def list_datasets(filters, project=None):
    """list datasets

    List datasets from backend with optional FILTERS. Uses PROJECT set via zpy project command when available.
    """
    from cli.datasets import fetch_datasets

    try:
        filters = parse_args(filters)
        if project:
            filters["project"] = project
    except Exception:
        click.secho(f"Failed to parse filters: {filters}", fg="yellow", err=True)
        return

    try:
        with Loader("Fetching datasets..."):
            datasets = fetch_datasets(filters)
        click.echo("Fetched datasets successfully.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch datasets {e}.", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
        return

    tbl = TableLogger(
        columns="id,project,name,state,type,created_at",
        colwidth={
            "id": UUID_WIDTH,
            "project": UUID_WIDTH,
            "name": LARGE_WIDTH,
            "state": SMALL_WIDTH,
            "type": SMALL_WIDTH,
            "created_at": DATETIME_WIDTH,
        },
    )
    for d in datasets:
        tbl(
            d["id"],
            d["project"],
            d["name"],
            d["state"].lower(),
            d["type"],
            d["created_at"],
        )


@cli_list.command("sims")
@click.argument("filters", nargs=-1)
@use_project()
def list_sims(filters, project=None):
    """list sims

    List sims from backend with optional FILTERS. Uses PROJECT set via zpy project command when available.
    """
    from cli.sims import fetch_sims

    try:
        filters = parse_args(filters)
        if project:
            filters["project"] = project
    except Exception:
        click.secho(f"Failed to parse filters: {filters}", fg="yellow", err=True)
        return

    try:
        with Loader("Fetching sims..."):
            sims = fetch_sims(filters)
        click.echo("Fetched sims successfully.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch sims {e}.", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
        return

    tbl = TableLogger(
        columns="id,project,name,state,zpy_version,blender_version,created_at",
        colwidth={
            "id": UUID_WIDTH,
            "project": UUID_WIDTH,
            "name": LARGE_WIDTH,
            "state": SMALL_WIDTH,
            "zpy_version": MEDIUM_WIDTH,
            "blender_version": SMALL_WIDTH,
            "created_at": DATETIME_WIDTH,
        },
    )
    for s in sims:
        tbl(
            s["id"],
            s["project"],
            s["name"],
            s["state"],
            s["zpy_version"],
            s["blender_version"],
            s["created_at"],
        )


@cli_list.command("projects")
@click.argument("filters", nargs=-1)
def list_projects(filters):
    """list projects

    List projects from backend with optional FILTERS.
    """
    from cli.projects import fetch_projects

    try:
        filters = parse_args(filters)
    except Exception:
        click.secho(f"Failed to parse filters: {filters}", fg="yellow", err=True)
        return

    try:
        with Loader("Fetching projects..."):
            projects = fetch_projects(filters)
        click.echo("Fetched projects successfully.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch projects {e}.", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
        return

    tbl = TableLogger(
        columns="id,name,account,created_at",
        colwidth={
            "id": UUID_WIDTH,
            "name": LARGE_WIDTH,
            "account": UUID_WIDTH,
            "created_at": DATETIME_WIDTH,
        },
    )
    for p in projects:
        tbl(
            p["id"],
            p["name"],
            p["account"],
            p["created_at"],
        )


@cli_list.command("accounts")
@click.argument("filters", nargs=-1)
def list_accounts(filters):
    """list accounts

    List accounts from backend with optional FILTERS.
    """
    from cli.accounts import fetch_accounts

    try:
        filters = parse_args(filters)
    except Exception:
        click.secho(f"Failed to parse filters: {filters}", fg="yellow", err=True)
        return

    try:
        with Loader("Fetching accounts..."):
            accounts = fetch_accounts(filters)
        click.echo("Fetched accounts successfully.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch accounts {e}.", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
        return

    tbl = TableLogger(
        columns="id,type,email,created_at",
        colwidth={
            "id": UUID_WIDTH,
            "type": LARGE_WIDTH,
            "email": UUID_WIDTH,
            "created_at": DATETIME_WIDTH,
        },
    )
    for p in accounts:
        tbl(
            p["id"],
            p["type"],
            p["email"],
            p["created_at"],
        )


@cli_list.command("jobs")
@click.argument("filters", nargs=-1)
@use_project()
def list_jobs(filters, project=None):
    """
    list jobs

    List jobs from backend with optional FILTERS. Uses PROJECT set via `zpy project` command when available.
    """
    from cli.jobs import fetch_jobs

    try:
        filters = parse_args(filters)
        if project:
            filters["project"] = project
    except Exception:
        click.secho(f"Failed to parse filters: {filters}", fg="yellow", err=True)
        return

    try:
        with Loader("Fetching jobs..."):
            jobs = fetch_jobs(filters)
        click.echo("Fetched jobs successfully.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch jobs {e}.", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
        return

    tbl = TableLogger(
        columns="id,state,name,operation,created_at",
        colwidth={
            "id": UUID_WIDTH,
            "state": SMALL_WIDTH,
            "name": LARGE_WIDTH,
            "operation": SMALL_WIDTH,
            "created_at": DATETIME_WIDTH,
        },
    )
    for j in jobs:
        tbl(j["id"], j["state"], j["name"], j["operation"], j["created_at"])


# ------- GET


@cli.group("get")
def get():
    """get object

    Get group is used for download commands on backend objects.
    """
    pass


@get.command("dataset")
@click.argument("name")
@click.argument("dtype", type=click.Choice(["job", "generated", "uploaded"]))
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
)
def get_dataset(name, dtype, path):
    """get dataset

    Download dataset of type DTYPE and name NAME to local PATH from backend.

    Args:
        name (str): name of dataset
        dtype (str): type of dataset
        path (str): directory to put zipped dataset
    """
    from cli.datasets import download_dataset

    try:
        output_path = download_dataset(name, path, dtype)
        click.echo(f"Downloaded {dtype} dataset '{name}' to {output_path}")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to download dataset: {e}", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
    except NameError as e:
        click.secho(f"Failed to download dataset: {e}", fg="yellow", err=True)


@get.command("sim")
@click.argument("name")
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
)
def get_sim(name, path):
    """get sim

    Download sim with name NAME from backend.

    Args:
        name (str): name of sim
        path (str): directory to put zipped sim
    """
    from cli.sims import download_sim

    try:
        output_path = download_sim(name, path)
        click.echo(f"Downloaded sim '{name}' to {output_path}")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to download sim: {e}", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
    except NameError as e:
        click.secho(f"Failed to download sim: {e}", fg="yellow", err=True)


# -------  UPLOAD


@cli.group("upload")
def upload():
    """upload object

    Upload group is used for upload commands on backend objects.
    """
    pass


@upload.command("sim")
@click.argument("name")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@use_project(required=True)
def upload_sim(name, path, project=None):
    """upload sim

    Upload sim located at PATH to PROJECT and call it NAME. Requires PROJECT to be set via `zpy project`.

    Args:
        name (str): name of sim
        path (str): path to sim
        project (str): project uuid
    """
    from cli.sims import create_sim

    if to_pathlib_path(path).suffix != ".zip":
        click.secho(f"File {path} must be of type zip", fg="red", err=True)
    try:
        with Loader("Uploading sim..."):
            create_sim(name, path, project)
        click.secho(f"Uploaded sim {path} with name '{name}'", fg="green")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to upload sim: {e}", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)


@upload.command("dataset")
@click.argument("name")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@use_project(required=True)
def upload_dataset(name, path, project=None):
    """upload dataset

    Upload dataset located at PATH to PROJECT and call it NAME. Requires PROJECT to be set via `zpy project`.

    Args:
        name (str): name of dataset
        path (str): path to dataset
        project (str): project uuid
    """
    from cli.datasets import create_uploaded_dataset

    if to_pathlib_path(path).suffix != ".zip":
        click.secho(f"File {path} must be of type zip", fg="red", err=True)
    try:
        with Loader("Uploading dataset..."):
            create_uploaded_dataset(name, path, project)
        click.secho(f"Uploaded dataset {path} with name '{name}'", fg="green")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to upload dataset: {e}", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)


# ------- CREATE


@cli.group("create")
def create():
    """create object

    Create group is used for create commands on backend objects.
    """
    pass


@create.command("project")
@click.argument("account", type=click.UUID)
@click.argument("name")
def create_project(account, name):
    """Create a project under ACCOUNT called NAME

    See available accounts: zpy list accounts
    """
    from cli.projects import create_project

    try:
        create_project(account, name)
        click.secho(f"Created project '{name}'", fg="green")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to create project: {e}", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)


@create.command("dataset")
@click.argument("name")
@click.argument("sim")
@click.argument("args", nargs=-1)
@use_project(required=True)
def create_dataset(name, sim, args, project=None):
    """Create a dataset.

    Create a generated dataset object called NAME. This will trigger the generation of data from SIM given the
    input ARGS. Requires PROJECT to be set via `zpy project`.

    Args:
        name (str): name of new dataset
        sim (str): name of sim dataset is built with
        args (List(str)): configuration of sim for this dataset
        project (str): project uuid
    """
    from cli.datasets import create_generated_dataset

    try:
        dataset_config = parse_args(args)
    except Exception:
        click.secho(f"Failed to parse args: {args}", fg="yellow", err=True)
        return
    try:
        create_generated_dataset(name, sim, parse_args(args), project)
        click.secho(
            f"Created dataset '{name}' from sim '{sim}' with config {dataset_config}",
            fg="green",
        )
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to create dataset: {e}", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
    except NameError as e:
        click.secho(f"Failed to create dataset: {e}", fg="yellow", err=True)


@create.command("sweep")
@click.argument("name")
@click.argument("sim")
@click.argument("number")
@click.argument("args", nargs=-1)
@use_project(required=True)
def create_sweep(name, sim, number, args, project=None):
    """create sweep

    Create a sweep of generated dataset objects called "NAME seed<i>" where i ranges from 0 to NUMBER - 1.
    These will trigger the generation of data from SIM given the input ARGS. Sweep is just a series of create dataset
    calls with different seeds set. Requires PROJECT to be set via `zpy project`.

    Args:
        name (str): name of new dataset
        sim (str): name of sim dataset is built with
        number (str): number of datasets to create
        args (List(str)): configuration of sim for this dataset
        project (str): project uuid
    """
    from cli.datasets import create_generated_dataset

    try:
        dataset_config = parse_args(args)
    except Exception:
        click.secho(f"Failed to parse args: {args}", fg="yellow", err=True)
        return
    for i in range(int(number)):
        dataset_name = f"{name} seed{i}"
        dataset_config["seed"] = i
        try:
            create_generated_dataset(dataset_name, sim, dataset_config, project)
            click.secho(
                f"Created dataset '{dataset_name}' from sim '{sim}' with config {dataset_config}",
                fg="green",
            )
        except requests.exceptions.HTTPError as e:
            click.secho(f"Failed to create dataset: {e}", fg="red", err=True)
            if e.response.status_code == 400:
                click.secho(str(e.response.json()), fg="red", err=True)
        except NameError as e:
            click.secho(f"Failed to create dataset: {e}", fg="yellow", err=True)
            return
    click.echo(f"Finished creating {number} datasets from sim '{sim}'.")


@create.command("job")
@click.argument("name")
@click.argument("operation", type=click.Choice(["package", "tvt", "train"]))
@click.option(
    "filters",
    "-f",
    multiple=True,
    help="Key/value pairs separated by spaces. Passed as query params in the API call to filter data sets.",
)
@click.option(
    "configfile",
    "--configfile",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help="Path to json file",
)
@click.option(
    "sweepfile",
    "--sweepfile",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help="Path to json file",
)
@use_project(required=True)
def create_job(name, operation, filters, configfile, sweepfile, project=None):
    """create job

    Create a job called NAME within PROJECT to perform OPERATION on a group of datasets defined by the FILTERS
    provided by -f. Requires PROJECT set via `zpy project`.
    """
    from cli.datasets import filter_datasets
    from cli.jobs import create_new_job

    filtered_datasets = []
    for dfilter in filters:
        try:
            with Loader(f"Filtering datasets by '{dfilter}'..."):
                datasets_by_type = filter_datasets(dfilter, project)

            for [dataset_type, datasets] in datasets_by_type.items():
                count = len(datasets)
                click.secho(f"Found {count} of type<{dataset_type}>")

                if count == 0:
                    continue

                dataset_names = list(datasets.values())
                print_list_as_columns(dataset_names)

            filtered_datasets_ids = [
                data_set_id
                for data_sets in datasets_by_type.values()
                for data_set_id in data_sets.keys()
            ]
            filtered_datasets.extend(filtered_datasets_ids)
        except requests.exceptions.HTTPError as e:
            click.secho(f"Failed to filter datasets {e}", fg="red", err=True)

    job_configs = []
    if configfile:
        config = read_json(configfile)
        job_configs.append(config)
        click.echo(f"Parsed config file {configfile} : {config}")
    elif sweepfile:
        sweep_config = read_json(sweepfile)
        try:
            configs = resolve_sweep(sweep_config)
        except Exception as e:
            click.secho(
                f"Failed to resolve sweep file {sweepfile} {e}", fg="yellow", err=True
            )
            return
        job_configs.extend(configs)
        click.echo(f"Parsed sweep file {sweepfile} : {sweep_config}")
    else:
        job_configs.append(dict())

    click.confirm(f"Launch {len(job_configs)} jobs?", abort=True)

    for i, config in enumerate(job_configs):
        job_name = name if i == 0 else f"{name} {i}"
        try:
            create_new_job(job_name, operation, config, filtered_datasets, project)
            click.secho(
                f"Created {operation} job '{job_name}' with config {config}", fg="green"
            )
        except requests.exceptions.HTTPError as e:
            click.secho(f"Failed to create job: {e}", fg="red", err=True)
            if e.response.status_code == 400:
                click.secho(str(e.response.json()), fg="red", err=True)

    click.echo(f"Finished creating {len(job_configs)} jobs with name '{name}'")


# ------- LOGS


@cli.group("logs")
def logs():
    """logs

    Logs group is used for fetching logs of object backend runs.
    """
    pass


@logs.command("dataset")
@click.argument("name")
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
)
def logs_dataset(name, path):
    """generated dataset logs

    Download generated dataset run logs.

    Args:
        name (str): name of dataset
        path (str): directory to put logs in
    """
    from cli.logs import fetch_logs

    try:
        fetch_logs("generated-data-sets", name, path)
        click.echo(f"Downloaded {path}/[info/debug/error].log from '{name}'.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch logs: {e}", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
    except NameError as e:
        click.secho(f"Failed to fetch logs: {e}", fg="yellow", err=True)


@logs.command("job")
@click.argument("name")
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True),
)
def logs_job(name, path):
    """job logs

    Download job run logs.

    Args:
        name (str): name of job
        path (str): directory to put logs in
    """
    from cli.logs import fetch_logs

    try:
        fetch_logs("jobs", name, path)
        click.echo(f"Downloaded {path}/[info/debug/error].log from '{name}'.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch logs: {e}", fg="red", err=True)
        if e.response.status_code == 400:
            click.secho(str(e.response.json()), fg="red", err=True)
    except NameError as e:
        click.secho(f"Failed to fetch logs: {e}", fg="yellow", err=True)
