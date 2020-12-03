"""
    Logging utilities.
"""
import logging
from typing import List

log = logging.getLogger(__name__)


def set_log_levels(
    level: str = None,
    modules: List[str] = [
        'zpy',
        # Addon modules
        'zpy_addon',
        'bpy.zpy_addon'
    ]
) -> None:
    """ Set logger levels for all zpy modules. """
    if level is None:
        log_level = logging.INFO
    elif level == 'info':
        log_level = logging.INFO
    elif level == 'debug':
        log_level = logging.DEBUG
    elif level == 'warning':
        log_level = logging.WARNING
    else:
        log.warning(f'Invalid log level {level}')
        return
    log.warning(f'Setting log level to {log_level}')
    for logger_name in modules:
        logging.getLogger(logger_name).setLevel(log_level)


def linebreaker_log(message: str, line_length: int = 80):
    """ Good looking line-breaker log message. """
    # Clip the message
    message = message[:line_length]
    whitespace = ' ' * int(line_length / 2 - len(message))
    # La piece de resistance
    log.info('-'*line_length)
    log.info(f'{whitespace}{message.upper()}{whitespace}')
    log.info('-'*line_length)