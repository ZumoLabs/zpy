"""
    Utilities for color.
"""
import logging
import random
from pathlib import Path
from typing import List, Tuple, Union

import zpy

log = logging.getLogger(__name__)

# Random colors are loaded on module import
RANDOM_COLOR_IDX = 1
COLORS_FILE = 'colors.json'
COLORS = None


def reset():
    """ Load colors from file and reset random idx. """
    global COLORS, RANDOM_COLOR_IDX
    _path = Path(__file__).parent / COLORS_FILE
    zpy.files.verify_path(_path)
    COLORS = zpy.files.read_json(_path)
    RANDOM_COLOR_IDX = 1


def hex_to_irgb(hex_value: str) -> Tuple[int]:
    """ Convert hex value to integer rgb (0 to 255). """
    hex_value = int(hex_value[1:], 16)
    b = (hex_value & 0xFF)
    g = ((hex_value >> 8) & 0xFF)
    r = ((hex_value >> 16) & 0xFF)
    return r, g, b


def frgb_to_frgba(rgb: Tuple[float], a=1.0) -> Tuple[float]:
    """ Convert 3-channel RGB to 4-channel RGBA. """
    _val = *rgb, a
    return _val


def hex_to_frgb(hex_value: str) -> Tuple[float]:
    """ Convert hex value to float rgb (0 to 1). """
    return irgb_to_frgb(hex_to_irgb(hex_value))


def irgb_to_frgb(irgb: Tuple[float]) -> Tuple[float]:
    """ Convert integer rgb (0 to 255) to float rgb (0 to 1). """
    r, g, b = irgb
    return r / 255.0, g / 255.0, b / 255.0


def irgb_to_hex(irgb: Tuple[float]) -> str:
    """ Convert integer rgb (0 to 255) to hex. """
    r, g, b = irgb
    return '#%02x%02x%02x' % (r, g, b)


def frgb_to_irgb(frgb: Tuple[float]) -> Tuple[int]:
    """ Convert float rgb (0 to 1) to integer rgb (0 to 255). """
    r, g, b = frgb
    return int(r * 255.0), int(g * 255.0), int(b * 255.0)


def frgb_to_hex(frgb: Tuple[float]) -> str:
    """ Convert float rgb (0 to 1) to hex. """
    return irgb_to_hex(frgb_to_irgb(frgb))


def frgb_to_srgba(frgb: Tuple[float], a=1.0) -> Tuple[float]:
    """ Convert float rgb (0 to 1) to the gamma-corrected sRGBA float (0 to 1). """
    return frgb[0]**(1/2.2), frgb[1]**(1/2.2), frgb[2]**(1/2.2), a


def frgb_to_srgb(frgb: Tuple[float]) -> Tuple[float]:
    """ Convert float rgb (0 to 1) to the gamma-corrected sRGB float (0 to 1). """
    return frgb[0]**(1/2.2), frgb[1]**(1/2.2), frgb[2]**(1/2.2)


def _output_style(name: str, hex: str, output_style: str) -> Union[Tuple[float, int, str], str]:
    """ Convert hex to an output style. """
    if output_style == 'frgb':
        return hex_to_frgb(hex)
    if output_style == 'frgba':
        return frgb_to_frgba(hex_to_frgb(hex))
    elif output_style == 'irgb':
        return hex_to_irgb(hex)
    elif output_style == 'hex':
        return hex
    elif output_style == 'name_irgb':
        return name, hex_to_irgb(hex)
    elif output_style == 'name_frgb':
        return name, hex_to_frgb(hex)
    elif output_style == 'name_frgba':
        return name, frgb_to_frgba(hex_to_frgb(hex))
    else:
        raise ValueError('Color must be frgb, irgb, or hex.')


def default_color(output_style: str = 'frgb') -> Union[Tuple[float, int, str], str]:
    """ Default color. """
    global COLORS
    if COLORS is None:
        reset()
    _name = COLORS[0]['name']
    _hex = COLORS[0]['hex']
    log.debug(
        f'Default color chosen is {_name} - {_hex} - {hex_to_frgb(_hex)}')
    return _output_style(_name, _hex, output_style=output_style)


def random_color(output_style: str = 'frgb') -> Union[Tuple[float, int, str], str]:
    """ Random color.

    This will go through a pre-baked list every time, 
    to prevent different random seeds from changing the
    color for a category.

    """
    global RANDOM_COLOR_IDX, COLORS
    if COLORS is None:
        reset()
    _name = COLORS[RANDOM_COLOR_IDX]['name']
    _hex = COLORS[RANDOM_COLOR_IDX]['hex']
    # Update global color idx
    RANDOM_COLOR_IDX += 1
    if RANDOM_COLOR_IDX > len(COLORS):
        log.error(f'Ran out of unique colors!')
    log.debug(f'Random color chosen is {_name} - {_hex} - {hex_to_frgb(_hex)}')
    return _output_style(_name, _hex, output_style=output_style)


def closest_color(color: Tuple[float],
                  colors: List[Tuple[float]],
                  max_dist: float = 0.01,
                  ) -> Union[None, Tuple[float]]:
    """ Get the index of the closest color in a list to the input color. """
    min_dist = 3.0
    nearest_idx = 0
    for i, _color in enumerate(colors):
        dist = (color[0] - _color[0])**2 + \
            (color[1] - _color[1])**2 + \
            (color[2] - _color[2])**2
        if dist < min_dist:
            min_dist = dist
            nearest_idx = i
    if min_dist > max_dist:
        log.debug(
            f'No color close enough w/ maxmimum distance of {max_dist}')
        return None
    return colors[nearest_idx]
