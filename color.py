"""
    Utilities for color.
"""
from typing import Dict, Union, Tuple, List
import logging
import numpy as np
import random
from pathlib import Path

from . import file

log = logging.getLogger(__name__)

# Random colors are loaded on module import
RANDOM_COLOR_IDX = 1
COLORS = file.read_json(Path(__file__).parent / 'colors.json')

def loadColors():
    
    return file.read_json(Path(__file__).parent / 'colors.json')

def hex_to_irgb(hex_value: str) -> Tuple[int]:
    """ Convert hex value to integer rgb (0 to 255). """
    hex_value = int(hex_value[1:], 16)
    b = (hex_value & 0xFF)
    g = ((hex_value >> 8) & 0xFF)
    r = ((hex_value >> 16) & 0xFF)
    return r, g, b

def rgb_to_rgba(rgb: Tuple[float], a = 1.0) -> Tuple[float]:
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




def random_color(output_style: str = 'frgb') -> Union[Tuple[float, int, str], str]:
    """ Random color in frgb, irgb, or hex.

    This will go through a pre-baked list every time, 
    to prevent different random seeds from changing the
    color for a category.

    """
    global RANDOM_COLOR_IDX, COLORS
    _name = COLORS[RANDOM_COLOR_IDX]['name']
    _hex = COLORS[RANDOM_COLOR_IDX]['hex']
    # Update global color idx
    RANDOM_COLOR_IDX += 1
    if RANDOM_COLOR_IDX > len(COLORS):
        log.error(f'Ran out of unique colors!')
    log.debug(f'Random color chosen is {_name}')
    if output_style == 'frgb':
        return hex_to_frgb(_hex)
    elif output_style == 'irgb':
        return hex_to_irgb(_hex)
    elif output_style == 'hex':
        return _hex
    elif output_style == 'name_irgb':
        return _name, hex_to_irgb(_hex)
    elif output_style == 'name_frgb':
        return _name, hex_to_frgb(_hex)
    else:
        raise ValueError('Color must be frgb, irgb, or hex.')


def random_color_line(output_style: str = 'frgb', line_number: int = 0) -> Union[Tuple[float, int, str], str]:
    """ Random color in frgb, irgb, or hex.

    This will go through a pre-baked list every time, 
    to prevent different random seeds from changing the
    color for a category.

    """
    # global RANDOM_COLOR_IDX, COLORS
    # Update global color idx

    colors=loadColors()
    random_color_idx = line_number
            
    if line_number==0:
        random_color_idx=random.randint(1,len(colors))
    # RANDOM_COLOR_IDX += 1
    
    
    
    _name = colors[random_color_idx]['name']
    _hex = colors[random_color_idx]['hex']
    
    if random_color_idx > len(colors):
        log.error(f'Ran out of unique colors!')
    log.debug(f'Random color chosen is {_name}')

    print("color: {} hex: {} rgb: {} ".format(_name, _hex, hex_to_frgb(_hex) ) )
    
    if output_style == 'frgb':
        return hex_to_frgb(_hex)
    elif output_style == 'irgb':
        return hex_to_irgb(_hex)
    elif output_style == 'hex':
        return _hex
    elif output_style == 'name_irgb':
        return _name, hex_to_irgb(_hex)
    elif output_style == 'name_frgb':
        return _name, hex_to_frgb(_hex)
    else:
        raise ValueError('Color must be frgb, irgb, or hex.')


def closest_color(color: Tuple[float],
                  colors: List[Tuple[float]],
                  max_cube_dist: float = 10,
                  ) -> Union[None, Tuple[float]]:
    """ Get the index of the closest color in a list to the input color. """
    color = frgb_to_hex(color)
    r, g, b = (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
    def cube(x): return x*x
    def f(hex_val, ref): return cube(int(hex_val, 16) - ref)
    min_cube_d = cube(0xFFFFFF)
    nearest_idx = 0
    for i, _color in enumerate(colors):
        _color = frgb_to_hex(_color)
        cube_d = f(_color[1:3], r) + f(_color[3:5], g) + f(_color[5:7], b)
        if cube_d < min_cube_d:
            min_cube_d = cube_d
            nearest_idx = i
    if min_cube_d > max_cube_dist:
        log.debug(
            f'No color close enough w/ maxmimum cube distance of {max_cube_dist}')
        return None
    return colors[nearest_idx]


def reset_rgb():
    """ return default rgb """

    return 1.0, 1.0, 1.0

def reset_rgba():
    """ return default rgba """

    return 1.0, 1.0, 1.0, 1.0