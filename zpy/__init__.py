from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# TODO: Some interaction between Blender's Python
# and Gin-Config requires this part below. If
# you know the answer: do let us know :)
from zpy import blender
from zpy import blender
from zpy import camera
from zpy import color
from zpy import file
from zpy import image
from zpy import keypoints
from zpy import material
from zpy import object
from zpy import render
from zpy import viz
from zpy import output
from zpy import output_coco
from zpy import output_mot
from zpy import output_zumo
from zpy import saver
from zpy import tvt