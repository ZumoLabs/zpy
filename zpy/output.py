"""
    Base class for new annotation formats. Any new annotation format must be
    able to take a saver object and output annotations.
"""
from zpy.saver import Saver


class Output:
    """Holds the logic for outputting annotations to file."""

    def __init__(self, saver: Saver):
        """ Initialize from a Saver object. """
        self.saver = saver

    def output_annotations(self):
        """ Output annotation file. """
        raise NotImplementedError('Must implement output_annotations()')
