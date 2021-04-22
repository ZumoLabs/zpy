import logging
from copy import deepcopy
from itertools import product

import click
from zpy.files import read_json, to_pathlib_path

from cli.config import initialize_config, login, read_config, switch_env
from cli.datasets import (create_generated_dataset, create_uploaded_dataset,
                          fetch_dataset, fetch_datasets, filter_dataset)
from cli.jobs import create_new_job, fetch_jobs
from cli.sims import create_sim, fetch_sim, fetch_sims
from cli.utils import parse_args

log = logging.getLogger(__name__)


@click.group(context_settings=dict(token_normalize_func=str.lower))
@click.option('--verbose', '-v', is_flag=True, help="Enables verbose mode.")
def cli(verbose=False):
    ''' zpy cli is client side ragnarok '''
    # Set up logging
    level = logging.INFO
    if verbose:
        level = logging.DEBUG
    logging.basicConfig(
        level=level, format='%(message)s')
    initialize_config()


@cli.command('help')
def _help():
    log.info('usage: zpy <command> [<args>]')


@cli.command('env')
@click.argument('env', type=click.Choice(['local', 'stage', 'prod']))
def _env(env):
    """ switch target environment """
    log.info(f'switching to environment {env}')
    switch_env(env)


@cli.command('login')
@click.argument('username')
@click.argument('password')
def _login(username, password):
    login(username, password)


@cli.command('config')
def _config():
    """ display config """
    config = read_config()
    log.info('zpy cli configuration:')
    log.info(config)


############
### LIST ###
############


@cli.group()
def list():
    """ list resources """
    pass


@list.command('datasets')
def list_datasets():
    fetch_datasets()


@list.command('sims')
def list_sims():
    fetch_sims()


@list.command('jobs')
def list_jobs():
    fetch_jobs()


###########
### GET ###
###########


@cli.group()
def get():
    """ get resource """
    pass


@get.command('dataset')
@click.argument('name')
@click.argument('dtype', type=click.Choice(['job', 'generated', 'uploaded']))
@click.argument('path')
def get_dataset(name, dtype, path):
    dir_path = to_pathlib_path(path)
    if not dir_path.exists():
        log.info(f'output path {dir_path} does not exist')
        return
    fetch_dataset(name, path, dtype)


@get.command('sim')
@click.argument('name')
@click.argument('path')
def get_sim(name, path):
    dir_path = to_pathlib_path(path)
    if not dir_path.exists():
        log.info(f'output path {dir_path} does not exist')
        return
    fetch_sim(name, path)

##############
### UPLOAD ###
##############


@cli.group()
def upload():
    """ upload resource """
    pass


@upload.command('sim')
@click.argument('name')
@click.argument('path')
def upload_sim(name, path):
    input_path = to_pathlib_path(path)
    if not input_path.exists():
        log.warning(f'input path {input_path} does not exist')
        return
    if input_path.suffix != '.zip':
        log.warning(f'input path {input_path} not a zip file')
    create_sim(name, path)


@upload.command('dataset')
@click.argument('name')
@click.argument('path')
def upload_dataset(name, path):
    input_path = to_pathlib_path(path)
    if not input_path.exists():
        log.info(f'input path {input_path} does not exist')
        return
    if input_path.suffix != '.zip':
        log.warning(f'input path {input_path} not a zip file')
    create_uploaded_dataset(name, path)


##############
### CREATE ###
##############


@cli.group()
def create():
    """ create resource """
    pass


@create.command('dataset')
@click.argument('name')
@click.argument('sim')
@click.argument('args', nargs=-1)
def create_dataset(name, sim, args):
    dataset_config = parse_args(args)
    create_generated_dataset(name, sim, dataset_config)


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
