from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# TODO: Why does Blender's Python want this pattern?
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