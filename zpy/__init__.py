# TODO: Why does Blender require this manual importing?
from . import blender
from . import color
from . import file
from . import material
from . import mesh
from . import render
from . import scene
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
