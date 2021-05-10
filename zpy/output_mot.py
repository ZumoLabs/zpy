"""
    MOT (Multi-Object Tracking) dataset format.

    https://motchallenge.net/faq/

"""
import logging
from pathlib import Path
from typing import Union

import gin
import zpy

log = logging.getLogger(__name__)


class MOTParseError(Exception):
    """Invalid MOT Annotation found when parsing data contents."""

    pass


@gin.configurable
class OutputMOT(zpy.output.Output):
    """Output class for MOT (Multi-Object Tracking) style annotations.

    https://motchallenge.net/faq/

    """

    ANNOTATION_FILENAME = Path("_annotations.mot.csv")

    def __init__(self, *args, **kwargs) -> Path:
        super().__init__(*args, annotation_filename=self.ANNOTATION_FILENAME, **kwargs)

    @gin.configurable
    def output_annotations(
        self,
        annotation_path: Union[Path, str] = None,
    ) -> Path:
        """Output MOT (Multi-Object Tracking) annotations to file.

        Args:
            annotation_path (Union[Path, str], optional): Output path for annotation file.

        Returns:
            Path: Path to annotation file.
        """
        annotation_path = super().output_annotations(annotation_path=annotation_path)
        mot = []
        for annotation in self.saver.annotations:
            if self.saver.images[annotation["image_id"]]["style"] != "default":
                # MOT annotations only have image annotations
                # for RGB images. No segmentation images.
                continue
            person_id = annotation.get("person_id", None)
            bbox = annotation.get("bbox", None)
            if (person_id is not None) and (bbox is not None):
                # Each CSV row will have 9 entries
                row = [0] * 9
                # Frame at which the object is present
                row[0] = annotation["frame_id"]
                # Pedestrian trajectory is identiﬁed by a unique ID
                row[1] = person_id
                # Coordinate of the top-left corner of the pedestrian bounding box
                row[2] = bbox[0]
                # Coordinate of the top-left corner of the pedestrian bounding box
                row[3] = bbox[1]
                # Width in pixels of the pedestrian bounding box
                row[4] = bbox[2]
                # Height in pixels of the pedestrian bounding box
                row[5] = bbox[3]
                # Flag whether the entry is to be considered (1) or ignored (0).
                row[6] = 1
                # TODO: Type of object annotated
                """
                MOT Types:
                    Pedestrian 1
                    Person on vehicle 2
                    Car 3
                    Bicycle 4
                    Motorbike 5
                    Non motorized vehicle 6
                    Static person 7
                    Distractor 8
                    Occluder 9
                    Occluder on the ground 10
                    Occluder full 11
                    Reflection 12
                    Crowd 13
                """
                row[7] = annotation["mot_type"]
                # TODO: Visibility ratio, a number between 0 and 1 that says how much of that object
                # is visible. Can be due to occlusion and due to image border cropping.
                row[8] = 1.0
                # Add to mot list
                mot.append(row)
        # Write out annotations to file
        zpy.files.write_csv(annotation_path, mot)
        # Verify annotations
        parse_mot_annotations(annotation_path)
        return annotation_path


@gin.configurable
def parse_mot_annotations(
    annotation_file: Union[Path, str],
) -> None:
    """Parse MOT annotations.

    Args:
        annotation_file (Union[Path, str]): Path to annotation file.

    Raises:
        MOTParseError: Rows are not length 9.
    """
    log.info(f"Verifying MOT annotations at {annotation_file}...")
    mot = zpy.files.read_csv(annotation_file)
    for row in mot:
        if not len(row) == 9:
            raise MOTParseError(
                f"Each row in MOT csv must have len 9, found len {len(row)}"
            )
    # TODO: Return Saver object.
