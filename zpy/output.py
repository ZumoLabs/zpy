"""
    Base class for outputing from a Saver object.
"""

from zpy.saver import Saver

class Output:
    """Holds the logic for outputting annotations to file."""

    def __init__(self, saver: Saver):
        """ Initialize from a Saver object. """
        self.saver = saver

    def output_annotations(self):
        """ Output ZUMO_META annotations.

        The ZUMO format is meant to be as close to
        a serialized version of this class as possbile.

        """
        raise NotImplementedError('Must implement output_annotations()')