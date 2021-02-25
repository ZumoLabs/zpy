from cli.config import login, initialize_config, switch_env, read_config
from cli.datasets import fetch_datasets, fetch_dataset, create_uploaded_dataset, create_generated_dataset, filter_dataset
from cli.scenes import fetch_scenes, fetch_scene, create_scene
from cli.jobs import fetch_jobs, create_new_job
from cli.utils import parse_args
from zpy.files import read_json, to_pathlib_path

import logging
import click

log = logging.getLogger(__name__)


@click.group()
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
    config = read_config()
    fetch_datasets(config['ENDPOINT'], config['TOKEN'])


@list.command('scenes')
def list_scenes():
    config = read_config()
    fetch_scenes(config['ENDPOINT'], config['TOKEN'])


@list.command('jobs')
def list_jobs():
    config = read_config()
    fetch_jobs(config['ENDPOINT'], config['TOKEN'])


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
    config = read_config()
    dir_path = to_pathlib_path(path)
    if not dir_path.exists():
        log.info(f'output path {dir_path} does not exist')
        return
    fetch_dataset(name, path, dtype, config['ENDPOINT'], config['TOKEN'])


@get.command('scene')
@click.argument('name')
@click.argument('path')
def get_scene(name, path):
    config = read_config()
    dir_path = to_pathlib_path(path)
    if not dir_path.exists():
        log.info(f'output path {dir_path} does not exist')
        return
    fetch_scene(name, path, config['ENDPOINT'], config['TOKEN'])

##############
### UPLOAD ###
##############

@cli.group()
def upload():
    """ upload resource """
    pass


@upload.command('scene')
@click.argument('name')
@click.argument('path')
def upload_scene(name, path):
    config = read_config()
    input_path = to_pathlib_path(path)
    if not input_path.exists():
        log.warning(f'input path {input_path} does not exist')
        return
    if input_path.suffix != '.zip':
        log.warning(f'input path {input_path} not a zip file')
    create_scene(name, path, config['ENDPOINT'], config['TOKEN'])


@upload.command('dataset')
@click.argument('name')
@click.argument('path')
def upload_dataset(name, path):
    config = read_config()
    input_path = to_pathlib_path(path)
    if not input_path.exists():
        log.info(f'input path {input_path} does not exist')
        return
    if input_path.suffix != '.zip':
        log.warning(f'input path {input_path} not a zip file')
    create_uploaded_dataset(name, path, config['ENDPOINT'], config['TOKEN'])


##############
### CREATE ###
##############


@cli.group()
def create():
    """ create resource """
    pass


@create.command('dataset')
@click.argument('name')
@click.argument('scene')
@click.argument('args', nargs=-1)
def create_dataset(name, scene, args):
    config = read_config()
    dataset_config = parse_args(args)
    create_generated_dataset(name, scene, dataset_config, config['ENDPOINT'], config['TOKEN'])


@create.command('job')
@click.argument('name')
@click.argument('operation')
@click.option('datasets', '-d', multiple=True)
@click.option('filters', '-f', multiple=True)
@click.option('configfile', '-configfile')
@click.argument('args', nargs=-1)
def create_job(name, operation, datasets, filters, configfile, args):
    config = read_config()
    if configfile:
        job_config = read_json(configfile)
    else:
        job_config = parse_args(args)
    datasets_list = [x for x in datasets]
    for dfilter in filters:
        datasets_list.extend(filter_dataset(dfilter, config['ENDPOINT'], config['TOKEN']))
    create_new_job(name, operation, job_config, datasets_list, config['ENDPOINT'], config['TOKEN'])
