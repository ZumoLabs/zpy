from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions

import logging as py_logging

log = py_logging.getLogger(__name__)

# Import files first since it is used in other zpy modules
from zpy import files

# Color utilities will reset the random colors on import
from zpy import color

color.reset()
from zpy import gin
from zpy import image
from zpy import logging
from zpy import requests

# Saver object (recording annotations at runtime)
from zpy import saver
from zpy import saver_image
from zpy import saver_video

# Output class (outputting annotations to file)
from zpy import output
from zpy import output_coco
from zpy import output_mot
from zpy import output_zumo
from zpy import output_csv

# If your zpy library has an extra dependency
# which may or may not be installed on a user's
# system, make sure to wrap it in a try-catch
try:
    from zpy import assets
    from zpy import blender
    from zpy import hdris
    from zpy import kdtree
    from zpy import keypoints
    from zpy import camera
    from zpy import material
    from zpy import nodes
    from zpy import objects
    from zpy import render
except ModuleNotFoundError:
    log.debug("Could not load blender utilities.")
try:
    from zpy import viz
except ModuleNotFoundError:
    log.debug("Could not load viz utilities.")
