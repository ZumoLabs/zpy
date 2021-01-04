from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# TODO: Some interaction between Blender's Python
# and Gin-Config requires this part below. If
# you know the answer: do let us know :)
try:
    from zpy import blender
    from zpy import keypoints
    from zpy import camera
    from zpy import material
    from zpy import object
    from zpy import render
except ModuleNotFoundError:
    # Load zpy without blender utils.
    pass
from zpy import color
# HACK: Reset the random colors on import
color.reset()
from zpy import file
from zpy import gin
from zpy import image
from zpy import logging
from zpy import requests
from zpy import tvt
from zpy import viz
# Output object
from zpy import output
from zpy import output_coco
from zpy import output_mot
from zpy import output_zumo
# Saver object
from zpy import saver
from zpy import saver_image
from zpy import saver_video