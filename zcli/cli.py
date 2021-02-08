from zcli.config import login, initialize_config, switch_env, read_config
from zcli.datasets import fetch_datasets, fetch_dataset
from zcli.scenes import fetch_scenes
from zcli.jobs import fetch_jobs
from zcli.utils import to_pathlib_path

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
    log.info(f'switching to environment {env}')
    switch_env(env)


@cli.command('login')
@click.argument('username')
@click.argument('password')
def _login(username, password):
    login(username, password)


@cli.command('config')
def _config():
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
    fetch_scene(name, path, config['ENDPOINT'], config['TOKEN'])


##############
### CREATE ###
##############


#@click.group()
#def create():
#    """ create resource """
#    pass
#
#@click.command('dataset')
#def create_dataset():
#    log.info('create dataset')
#
#@click.command('scene')
#def create_scene():
#    log.info('create scene')
#
#create.add_command(create_dataset)
#create.add_command(create_scene)

# Commands

#zpy.add_command(_help)
#zpy.add_command(_env)
#zpy.add_command(_login)
#zpy.add_command(list)
#zpy.add_command(fetch)
#zpy.add_command(create)
