"""
    Gin-config utilities.
"""
import logging
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, Tuple

import gin
import zpy

log = logging.getLogger(__name__)

# HACK: Conversion from zpy keys to human-readable keys
HUMAN_CONVERSION = {
    'seed': 'zpy.blender.set_seed.seed',
    'output_dir': 'zpy.saver.Saver.output_dir',
    'output_path': 'zpy.saver.Saver.output_dir',
    'num_images': 'zpy.blender.step.num_steps',
    'num_frames': 'zpy.blender.step.num_steps',
}


def replace_human_redable_kwargs(gin_bindings: Dict) -> Tuple[str, Any]:
    """ Replace any human readable versions of bindings. """
    log.info('Converting human readable bindings to gin...')
    for key, value in gin_bindings.items():
        if HUMAN_CONVERSION.get(key, None) is not None:
            log.info(f'Converted {key} to {HUMAN_CONVERSION[key]}')
            yield HUMAN_CONVERSION[key], value
        else:
            yield key, value


def parse_gin_bindings(
    gin_bindings: Dict = None,
) -> None:
    """ Parse any extra gin bindings to the config. """
    if gin_bindings is None:
        log.info(f'No additional gin bindings to parse')
    else:
        log.info(f'Parsing additional bindings: {pformat(gin_bindings)}')
        with gin.unlock_config():
            for key, value in replace_human_redable_kwargs(gin_bindings):
                try:
                    gin.bind_parameter(key, value)
                    _message = 'BOUND  '
                except:
                    _message = 'IGNORED'
                log.info(f'{_message} - {key} : {value}')


def parse_gin_config(
    gin_config: str = None,
    gin_config_dir: str = '$CONFIG',
) -> None:
    """ Parse a gin config file by path. """
    if gin_config is None:
        log.info(f'No gin file to parse.')
    else:
        gin_config_dir = zpy.files.verify_path(gin_config_dir, check_dir=True)
        if not gin_config.endswith('.gin'):
            gin_config = gin_config + '.gin'
        gin_config_filename = Path(gin_config)
        gin_config_path = gin_config_dir / gin_config_filename
        log.info(f'Parsing gin config at {gin_config_path}')
        if not gin_config_path.exists():
            raise zpy.requests.InvalidRequest(
                f'Could not find gin config at {gin_config_path}')
        gin.clear_config()
        gin.parse_config_file(str(gin_config_path))


def parse_gin_in_request(request: Dict) -> None:
    """ Parse any gin related keys in a request dict. """
    zpy.gin.parse_gin_config(gin_config=request.get('gin_config', None))
    zpy.gin.parse_gin_bindings(gin_bindings=request.get('gin_bindings', None))
    gin.finalize()
