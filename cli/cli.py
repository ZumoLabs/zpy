from copy import deepcopy
from itertools import product
from requests.auth import HTTPBasicAuth
import click
import logging
import requests
import json

from zpy.files import read_json, to_pathlib_path

from cli.config import initialize_config, read_config, write_config
from cli.datasets import (create_generated_dataset, create_uploaded_dataset,
                          download_dataset, fetch_datasets, filter_dataset)
from cli.jobs import create_new_job, fetch_jobs
from cli.sims import create_sim, fetch_sims
from cli.utils import parse_args

from cli.loader import Loader
from table_logger import TableLogger


@click.group(context_settings=dict(token_normalize_func=str.lower))
def cli():
    """ zpy cli

    Zumo Labs cli which is used to create, get, list, upload objects from
    the Zumo Labs backend (ragnarok).
    """
    initialize_config()


@cli.command('help')
def help():
    """ display help

    This will display help in order to provide users with more information
    on how to use this tool.
    """
    # TODO: spec this out
    click.echo('usage: zpy <command> [<args>]')


@cli.command('env')
@click.argument('env', type=click.Choice(['local', 'stage', 'prod']))
def env(env):
    """ switch target environment 

    This command allows zumo labs developers to swap the endpoint that the 
    cli communicates with. Unlikely to be relevant for non-zumo devs.

    Args:
        env (str): new environment for endpoint
    """
    config = read_config()
    config['ENVIRONMENT'] = env
    config['ENDPOINT'] = cli.config.ENDPOINTS[env]
    config['TOKEN'] = None
    write_config(config)
    click.echo(f'Target environment now {env}')
    click.echo("'zpy login' to fetch token")


@cli.command('login')
@click.argument('username', required=True)
@click.password_option(help="The login password.")
def login(username, password):
    """ login to ragnarok

    This command will update the zpy config with a token that is fetched
    from the backend using account details. 
    
    Accounts can be created at: app.zumolabs.ai

    Args:
        username (str): developer username
        password (str): developer password
    """
    config = read_config()
    endpoint = f"{config['ENDPOINT']}/auth/login/"
    click.echo(f'Login {endpoint}')
    r = requests.post(endpoint, auth=HTTPBasicAuth(username, password))
    if r.status_code != 200:
        click.echo('Login failed', err=True)
        return
    config['TOKEN'] = r.json()['token']
    write_config(config)
    click.echo('Login successful')


@cli.command('config')
def config():
    """ display config 

    Display current configuration file to developer.
    """
    pretty_config = json.dumps(read_config(), indent=2)
    click.echo(f'Zpy configuration:\n{pretty_config}')


############
### LIST ###
############


@cli.group()
def list():
    """ list objects

    List group is used for list commands on backend objects.
    """
    pass


@list.command('datasets')
def list_datasets():
    """ list datasets

    List datasets from backend.
    """
    from cli.datasets import fetch_datasets
    try:
        with Loader("Fetching sims..."):
            datasets = fetch_datasets()
        click.echo(f'Fetched datasets succesfully.')
    except requests.exceptions.HTTPError as e:
        click.secho(f'Failed to fetch datasets {e}.', fg='red', err=True)
        return

    tbl = TableLogger(columns='name,state,type,created,id')
    for d in datasets:
        tbl(d['name'], d['state'], d['type'], d['created_at'], d['id'])


@list.command('sims')
def list_sims():
    """ list datasets

    List sims from backend.
    """
    from cli.sims import fetch_sims
    try:
        with Loader("Fetching sims..."):
            sims = fetch_sims()
        click.echo(f'Fetched sims succesfully.')
    except requests.exceptions.HTTPError as e:
        click.secho(f'Failed to fetch sims {e}.', fg='red', err=True)
        return

    tbl = TableLogger(
        columns='name,state,zpy_version,blender_version,created', default_colwidth=30)
    for s in sims:
        tbl(s['name'], s['state'], s['zpy_version'],
            s['blender_version'], s['created_at'])


@list.command('jobs')
def list_jobs():
    """ list jobs

    List jobs from backend.
    """
    from cli.jobs import fetch_jobs
    try:
        with Loader("Fetching jobs..."):
            jobs = fetch_jobs()
        click.echo(f'Fetched jobs succesfully.')
    except requests.exceptions.HTTPError as e:
        click.secho(f'Failed to fetch jobs {e}.', fg='red', err=True)
        return

    tbl = TableLogger(columns='state,name,operation,created',default_colwidth=30)
    for j in jobs:
        tbl(j['state'], j['name'], j['operation'], j['created_at'])


###########
### GET ###
###########


@cli.group()
def get():
    """ get object

    Get group is used for download commands on backend objects.
    """
    pass


@get.command('dataset')
@click.argument('name')
@click.argument('dtype', type=click.Choice(['job', 'generated', 'uploaded']))
@click.argument(
    'path', 
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True)
)
def get_dataset(name, dtype, path):
    """ get dataset

    Download dataset from backend.

    Args:
        name (str): name of dataset
        dtype (str): type of dataset
        path (str): directory to put zipped dataset
    """
    from cli.datasets import download_dataset
    try:
        output_path = download_dataset(name, path, dtype)
        click.echo(f'Downloaded {dtype} dataset {name} to {output_path}')
    except requests.exceptions.HTTPError as e:
        click.secho(f'Failed to download dataset {e}', fg='red', err=True)
    except NameError as e:
        click.secho(f'Failed to download dataset {e}', fg='yellow', err=True)


@get.command('sim')
@click.argument('name')
@click.argument(
    'path', 
    type=click.Path(exists=True, file_okay=False, writable=True, resolve_path=True)
)
def get_sim(name, path):
    """ get sim

    Download sim from backend.

    Args:
        name (str): name of sim
        path (str): directory to put zipped sim
    """
    from cli.sims import download_sim
    try:
        output_path = download_sim(name, path)
        click.echo(f'Downloaded sim {name} to {output_path}')
    except requests.exceptions.HTTPError as e:
        click.secho(f'Failed to download sim {e}', fg='red', err=True)
    except NameError as e:
        click.secho(f'Failed to download sim {e}', fg='yellow', err=True)


##############
### UPLOAD ###
##############


@cli.group()
def upload():
    """ upload object

    Upload group is used for upload commands on backend objects.
    """
    pass


@upload.command('sim')
@click.argument('name')
@click.argument(
    'path', 
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
def upload_sim(name, path):
    """ upload sim

    Upload sim to backend.

    Args:
        name (str): name of sim
        path (str): path to sim
    """
    from cli.sims import create_sim
    if to_pathlib_path(path).suffix != '.zip':
        click.secho(f'File {path} must be of type zip', fg='red', err=True)
    try:
        create_sim(name, path)
        click.echo(f'Uploaded sim {path} with name {name}')
    except requests.exceptions.HTTPError as e:
        click.secho(f'Failed to upload sim {e}', fg='red', err=True)


@upload.command('dataset')
@click.argument('name')
@click.argument(
    'path', 
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
def upload_dataset(name, path):
    """ upload dataset

    Upload dataset to backend.

    Args:
        name (str): name of dataset
        path (str): path to dataset
    """
    from cli.datasets import create_uploaded_dataset   
    if to_pathlib_path(path).suffix != '.zip':
        click.secho(f'File {path} must be of type zip', fg='red', err=True)
    try:
        create_uploaded_dataset(name, path)
        click.echo(f'Uploaded dataset {path} with name {name}')
    except requests.exceptions.HTTPError as e:
        click.secho(f'Failed to upload datset {e}', fg='red', err=True)


##############
### CREATE ###
##############


@cli.group()
def create():
    """ create object

    Create group is used for create commands on backend objects.
    """
    pass


@create.command('dataset')
@click.argument('name')
@click.argument('sim')
@click.argument('args', nargs=-1)
def create_dataset(name, sim, args):
    dataset_config = parse_args(args)
    create_generated_dataset(name, sim, dataset_config)


@create.command('sweep')
@click.argument('name')
@click.argument('sim')
@click.argument('number')
@click.argument('args', nargs=-1)
def create_sweep(name, sim, number, args):
    dataset_config = parse_args(args)
    for i in range(int(number)):
        dataset_name = f'{name} seed{i}'
        dataset_config['seed'] = i
        create_generated_dataset(dataset_name, sim, dataset_config)


@create.command('job')
@click.argument('name')
@click.argument('operation')
@click.option('filters', '-f', multiple=True)
@click.option('configfile', '-configfile')
@click.option('sweepfile', '-sweepfile')
@click.argument('args', nargs=-1)
def create_job(name, operation, filters, configfile, sweepfile, args):
    datasets_list = []
    for dfilter in filters:
        datasets_list.extend(filter_dataset(dfilter))

    if sweepfile:
        sweep_config = read_json(sweepfile)
        bindings = sweep_config['gin_bindings']
        for c, random_binding in enumerate([dict(zip(bindings, v)) for v in product(*bindings.values())]):
            job_name = f'{name} {c}'
            job_config = deepcopy(sweep_config)
            job_config['gin_bindings'] = random_binding
            create_new_job(job_name, operation, job_config, datasets_list)
        return

    if configfile:
        job_config = read_json(configfile)
    else:
        job_config = parse_args(args)
    create_new_job(name, operation, job_config, datasets_list)
