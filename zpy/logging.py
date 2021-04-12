"""
    Logging utilities.
"""
from pathlib import Path
from typing import List, Union
import numpy as np
import logging
import shutil

log = logging.getLogger(__name__)


def set_log_levels(
    level: str = None,
    modules: List[str] = [
        'zpy',
        'zpy_addon',
        'bpy.zpy_addon'
        'neuralyzer',
        'bender',
    ],
) -> None:
    """ Set logger levels for all zpy modules.

    Args:
        level (str, optional): log level in [info, debug, warning]. Defaults to logging.Info.
        modules (List[str], optional): Modules to set logging for. Defaults to [ 'zpy', 'zpy_addon', 'bpy.zpy_addon' 'neuralyzer', ].
    """
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
    log.warning(f'Setting log level to {log_level} ({level})')
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s: %(levelname)s %(filename)s] %(message)s')
    for logger_name in modules:
        try:
            logging.getLogger(logger_name).setLevel(log_level)
        except:
            pass


def linebreaker_log(
    message: str,
    line_length: int = 80,
):
    """ Good looking line-breaker log message.

    Args:
        message (str): Message to put in the log.
        line_length (int, optional): Length of line breakers ----. Defaults to 80.
    """
    # Clip the message
    message = message[:line_length]
    whitespace = ' ' * int((line_length - len(message)) / 2)
    # La piece de resistance
    log.info('-'*line_length)
    log.info(f'{whitespace}{message.upper()}{whitespace}')
    log.info('-'*line_length)


def setup_file_handlers(
    log_dir: Union[str, Path] = '/tmp',
    error_log: bool = True,
    debug_log: bool = True,
) -> None:
    """ Output log files for requests

    Args:
        error_log: output error.log
        debug_log: output debug.log
        log_dir: directory to output log files
    """
    root = logging.getLogger()

    info_fh = logging.FileHandler(f"{log_dir}/info.log", mode="w")
    info_fh.setLevel(logging.INFO)
    root.addHandler(info_fh)

    if error_log:
        error_fh = logging.FileHandler(f"{log_dir}/error.log", mode="w")
        error_fh.setLevel(logging.ERROR)
        root.addHandler(error_fh)

    if debug_log:
        debug_fh = logging.FileHandler(f"{log_dir}/debug.log", mode="w")
        debug_fh.setLevel(logging.DEBUG)
        root.addHandler(debug_fh)


def save_log_files(
    output_dir: Union[str, Path],
    log_dir: Union[str, Path] = '/tmp',
) -> None:
    """ Save log files to output directory

    Args:
        output_dir: directory to save log files
        log_dir: directory where logs exist
    """
    for log in ['info.log', 'debug.log', 'error.log']:
        src = Path(log_dir) / log
        dst = Path(output_dir) / log
        if src.exists() and src != dst:
            shutil.copy(src, dst)


def parse_log_file(
    log_file: Union[str, Path]
) -> None:
    import re
    step_times, render_times = [], []
    with open(log_file, 'r') as f:
        render_in_step = []
        for l in f.readlines():
            seconds = re.search('\d+\.\d+(?=s)', l)
            if l.startswith('Rendering took'):
                render_in_step.append(float(seconds.group(0)))
            elif l.startswith('Simulation step took'):
                render_times.append(render_in_step)
                render_in_step = []
                step_times.append(float(seconds.group(0)))

    return {
        'avg_step_time': sum(step_times) / len(step_times),
        'avg_render_time': [v / len(render_times) for v in np.sum(render_times, axis=0)],
        'step_times': step_times,
        'render_times': render_times,
    }
