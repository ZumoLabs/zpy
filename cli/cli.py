from cli.loader import Loader
from cli.utils import parse_args, resolve_sweep
from cli.config import initialize_config, read_config, write_config, get_endpoint
from requests.auth import HTTPBasicAuth
from table_logger import TableLogger
from zpy.files import read_json, to_pathlib_path
import click
import json
import requests


@click.group(context_settings=dict(token_normalize_func=str.lower))
def cli():
    """zpy cli

    Zumo Labs cli which is used to create, get, list, upload objects from
    the Zumo Labs backend (ragnarok).
    """
    initialize_config()


@cli.command("help")
def help():
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
def env(env):
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
def config():
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


@cli.group()
def list():
    """list objects

    List group is used for list commands on backend objects.
    """
    pass


@list.command("datasets")
def list_datasets():
    """list datasets

    List datasets from backend.
    """
    from cli.datasets import fetch_datasets

    try:
        with Loader("Fetching datasets..."):
            datasets = fetch_datasets()
        click.echo("Fetched datasets succesfully.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch datasets {e}.", fg="red", err=True)
        return

    tbl = TableLogger(columns="name,state,type,created,id", default_colwidth=30)
    for d in datasets:
        tbl(d["name"], d["state"].lower(), d["type"], d["created_at"], d["id"])


@list.command("sims")
def list_sims():
    """list sims

    List sims from backend.
    """
    from cli.sims import fetch_sims

    try:
        with Loader("Fetching sims..."):
            sims = fetch_sims()
        click.echo("Fetched sims succesfully.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch sims {e}.", fg="red", err=True)
        return

    tbl = TableLogger(
        columns="name,state,zpy_version,blender_version,created", default_colwidth=30
    )
    for s in sims:
        tbl(
            s["name"],
            s["state"],
            s["zpy_version"],
            s["blender_version"],
            s["created_at"],
        )


@list.command("jobs")
def list_jobs():
    """list jobs

    List jobs from backend.
    """
    from cli.jobs import fetch_jobs

    try:
        with Loader("Fetching jobs..."):
            jobs = fetch_jobs()
        click.echo("Fetched jobs succesfully.")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to fetch jobs {e}.", fg="red", err=True)
        return

    tbl = TableLogger(columns="state,name,operation,created", default_colwidth=30)
    for j in jobs:
        tbl(j["state"], j["name"], j["operation"], j["created_at"])


# ------- GET


@cli.group()
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

    Download dataset from backend.

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

    Download sim from backend.

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
    except NameError as e:
        click.secho(f"Failed to download sim: {e}", fg="yellow", err=True)


# -------  UPLOAD


@cli.group()
def upload():
    """upload object

    Upload group is used for upload commands on backend objects.
    """
    pass


@upload.command("sim")
@click.argument("name")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def upload_sim(name, path):
    """upload sim

    Upload sim to backend.

    Args:
        name (str): name of sim
        path (str): path to sim
    """
    from cli.sims import create_sim

    if to_pathlib_path(path).suffix != ".zip":
        click.secho(f"File {path} must be of type zip", fg="red", err=True)
    try:
        with Loader("Uploading sim..."):
            create_sim(name, path)
        click.secho(f"Uploaded sim {path} with name '{name}'", fg="green")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to upload sim: {e}", fg="red", err=True)


@upload.command("dataset")
@click.argument("name")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def upload_dataset(name, path):
    """upload dataset

    Upload dataset to backend.

    Args:
        name (str): name of dataset
        path (str): path to dataset
    """
    from cli.datasets import create_uploaded_dataset

    if to_pathlib_path(path).suffix != ".zip":
        click.secho(f"File {path} must be of type zip", fg="red", err=True)
    try:
        with Loader("Uploading dataset..."):
            create_uploaded_dataset(name, path)
        click.secho(f"Uploaded dataset {path} with name '{name}'", fg="green")
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to upload dataset: {e}", fg="red", err=True)


# ------- CREATE


@cli.group()
def create():
    """create object

    Create group is used for create commands on backend objects.
    """
    pass


@create.command("dataset")
@click.argument("name")
@click.argument("sim")
@click.argument("args", nargs=-1)
def create_dataset(name, sim, args):
    """create dataset

    Create a generated dataset object in backend that will trigger
    the generation of the dataset.

    Args:
        name (str): name of new dataset
        sim (str): name of sim dataset is built with
        args (List(str)): configuration of sim for this dataset
    """
    from cli.datasets import create_generated_dataset

    try:
        dataset_config = parse_args(args)
    except Exception:
        click.secho("Failed to parse args: {args}", fg="yellow", err=True)
        return
    try:
        create_generated_dataset(name, sim, parse_args(args))
        click.secho(
            f"Created dataset '{name}' from sim '{sim}' with config {dataset_config}",
            fg="green",
        )
    except requests.exceptions.HTTPError as e:
        click.secho(f"Failed to create dataset: {e}", fg="red", err=True)
    except NameError as e:
        click.secho(f"Failed to create dataset: {e}", fg="yellow", err=True)


@create.command("sweep")
@click.argument("name")
@click.argument("sim")
@click.argument("number")
@click.argument("args", nargs=-1)
def create_sweep(name, sim, number, args):
    """create sweep

    Create a sweep of generated dataset object in backend that will trigger
    the generation of the dataset. Sweep is just a series of create dataset
    calls with different seeds set.

    Args:
        name (str): name of new dataset
        sim (str): name of sim dataset is built with
        number (str): number of datasets to create
        args (List(str)): configuration of sim for this dataset
    """
    from cli.datasets import create_generated_dataset

    try:
        dataset_config = parse_args(args)
    except Exception:
        click.secho("Failed to parse args: {args}", fg="yellow", err=True)
        return
    for i in range(int(number)):
        dataset_name = f"{name} seed{i}"
        dataset_config["seed"] = i
        try:
            create_generated_dataset(dataset_name, sim, dataset_config)
            click.secho(
                f"Created dataset '{dataset_name}' from sim '{sim}' with config {dataset_config}",
                fg="green",
            )
        except requests.exceptions.HTTPError as e:
            click.secho(f"Failed to create dataset: {e}", fg="red", err=True)
        except NameError as e:
            click.secho(f"Failed to create dataset: {e}", fg="yellow", err=True)
            return
    click.echo(f"Finished creating {number} datasets from sim '{sim}'.")


@create.command("job")
@click.argument("name")
@click.argument("operation")
@click.option("filters", "-f", multiple=True)
@click.option(
    "configfile",
    "--configfile",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
@click.option(
    "sweepfile",
    "--sweepfile",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
def create_job(name, operation, filters, configfile, sweepfile):
    """create job

    Create a job object in backend that will trigger an operation on
    datasets filtered by the filters.

    Args:
        name (str): name of new job
        operation (str): name of operation to run on datasets
        filters (str): string filters for dataset names to run job on
        configfile (str): json configuration for the job
        sweepfile (str): sweep json to launch a suite of jobs
    """
    from cli.datasets import filter_datasets
    from cli.jobs import create_new_job

    datasets = []
    for dfilter in filters:
        try:
            with Loader(f"Filtering datasets by '{dfilter}'..."):
                filtered_datasets = filter_datasets(dfilter)
            filtered_datasets_names = [*filtered_datasets.keys()]
            click.echo(
                f"Filtered datasets by filter '{dfilter}':\n{filtered_datasets_names}"
            )
            datasets.append(filtered_datasets.values())
        except requests.exceptions.HTTPError as e:
            click.secho(f"Failed to filter datsets {e}", fg="red", err=True)

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
            create_new_job(job_name, operation, config, datasets)
            click.secho(
                f"Created {operation} job '{job_name}' with config {config}", fg="green"
            )
        except requests.exceptions.HTTPError as e:
            click.secho(f"Failed to create job: {e}", fg="red", err=True)

    click.echo(f"Finished creating {len(job_configs)} jobs with name '{name}'")


# ------- LOGS


@cli.group()
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
    except NameError as e:
        click.secho(f"Failed to fetch logs: {e}", fg="yellow", err=True)
