"""
    CSV (comma separated value) dataset format.
"""
import logging
from pathlib import Path
from typing import Callable, List, Union

import gin
import zpy

log = logging.getLogger(__name__)


class CSVParseError(Exception):
    """Invalid CSV Annotation found when parsing data contents."""

    pass


@gin.configurable
class OutputCSV(zpy.output.Output):
    """Output class for CSV (comma separated value) style annotations."""

    ANNOTATION_FILENAME = Path("annotations.csv")

    def __init__(self, *args, **kwargs) -> Path:
        super().__init__(*args, annotation_filename=self.ANNOTATION_FILENAME, **kwargs)

    @gin.configurable
    def output_annotations(
        self,
        annotation_path: Union[Path, str] = None,
        annotation_dict_to_csv_row_func: Callable = None,
        header: List[str] = None,
    ) -> Path:
        """Output CSV annotations to file.

        Args:
            annotation_path (Union[Path, str], optional): Output path for annotation file.
            annotation_dict_to_csv_row_func (Callable, optional): Function that converts an annotation dict to csv row.
                Defaults to None.
            header (List[str], optional): Column headers. Defaults to None.

        Returns:
            Path: Path to annotation file.
        """
        annotation_path = super().output_annotations(annotation_path=annotation_path)
        if annotation_dict_to_csv_row_func is None:
            raise CSVParseError(
                "Output CSV annotations requires a annotation_dict_to_csv_row_func"
            )
        csv_data = []
        if header is not None:
            csv_data.append(header)
        for annotation in self.saver.annotations:
            row = annotation_dict_to_csv_row_func(annotation, saver=self.saver)
            if row is not None:
                csv_data.append(row)
        # Write out annotations to file
        zpy.files.write_csv(annotation_path, csv_data)
        # Verify annotations
        parse_csv_annotations(annotation_path)
        return annotation_path


@gin.configurable
def parse_csv_annotations(
    annotation_file: Union[Path, str],
) -> None:
    """Parse CSV annotations.

    Args:
        annotation_file (Union[Path, str]): Path to annotation file.

    Raises:
        CSVParseError: Rows not same length.
    """
    log.info(f"Verifying CSV annotations at {annotation_file}...")
    csv_data = zpy.files.read_csv(annotation_file)
    # Make sure all the rows are the same length
    csv_data_iterable = iter(csv_data)
    try:
        length = len(next(csv_data_iterable))
    except StopIteration:
        raise CSVParseError(f"No data found in CSV at {annotation_file}")
    log.debug(f"Row length in CSV: {[length for l in csv_data_iterable]}")
    if not all(len(row) == length for row in csv_data_iterable):
        raise CSVParseError(f"Not all rows in the CSV have same length {length}")
    # TODO: Return Saver object.
