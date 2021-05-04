"""
    Base class for new annotation formats. Any new annotation format must be
    able to take a saver object and output annotations.
"""
import logging
from pathlib import Path
from typing import Union

import zpy

log = logging.getLogger(__name__)


class Output:
    """Outputs a Saver object to various annotation file formats."""

    def __init__(
        self,
        saver: zpy.saver.Saver = None,
        annotation_filename: Union[Path, str] = "annotations.txt",
    ):
        """Create an Output object from a Saver object.

        Args:
            saver (zpy.saver.Saver, optional): Saver contains annotation and category information.
            annotation_filename (Union[Path, str], optional): Default name for annotation files.
        """
        if saver is not None:
            self.saver = saver
            # Try and deduce the annotation path from the saver object
            if self.saver.annotation_path is not None:
                self.annotation_path = self.saver.annotation_path
            elif self.saver.output_dir is not None:
                self.annotation_path = self.saver.output_dir / annotation_filename
            else:
                self.annotation_path = None
                log.warning("No annotation path could be deduced from Saver object.")

    def output_annotations(
        self,
        annotation_path: Union[Path, str] = None,
    ) -> Path:
        """Output annotations to file.

        Args:
            annotation_path (Union[Path, str], optional): Output path for annotation file.

        Returns:
            Path: Path to annotation file.
        """
        if annotation_path is None:
            annotation_path = self.annotation_path
        log.info(f"Outputting annotation file to {annotation_path}")
        annotation_path = zpy.files.verify_path(annotation_path)
        return annotation_path
