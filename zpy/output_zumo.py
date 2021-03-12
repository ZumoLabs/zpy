"""
    ZUMO dataset format.
"""
import logging
from pathlib import Path
from typing import Dict, Union

import gin
import zpy

log = logging.getLogger(__name__)


class ZUMOParseError(Exception):
    """ Invalid ZUMO Annotation found when parsing data contents. """
    pass


@gin.configurable
class OutputZUMO(zpy.output.Output):
    """ Output class for ZUMO style annotations.

    The ZUMO format is basically a serialized version of zpy.saver.Saver.

    """

    ANNOTATION_FILENAME = Path('ZUMO_META.json')

    def __init__(self, *args, **kwargs) -> Path:
        super().__init__(*args, annotation_filename=self.ANNOTATION_FILENAME, **kwargs)

    def output_annotations(self,
                           annotation_path: Union[Path, str] = None,
                           ) -> Path:
        """ Output annotations to file.

        Args:
            annotation_path (Union[Path, str], optional): Output path for annotation file.

        Returns:
            Path: Path to annotation file.
        """
        annotation_path = super().output_annotations(annotation_path=annotation_path)
        zumo_dict = {
            'metadata': self.saver.metadata,
            'categories': self.saver.categories,
            'images': self.saver.images,
            'annotations': self.saver.annotations,
        }
        # Write out annotations to file
        zpy.files.write_json(annotation_path, zumo_dict)
        # Verify annotations
        parse_zumo_annotations(
            annotation_file=annotation_path, data_dir=self.saver.output_dir)
        return annotation_path


@gin.configurable
def parse_zumo_annotations(
    annotation_file: Union[Path, str],
    data_dir: Union[Path, str] = None,
    output_saver: bool = False,
) -> zpy.saver_image.ImageSaver:
    """ Parse COCO annotations, optionally output a ImageSaver object.

    Args:
        annotation_file (Union[Path, str]): Path to annotation file.
        data_dir (Union[Path, str], optional): Directory containing data (images, video, etc).
        output_saver (bool, optional): Whether to return a Saver object or not. Defaults to False.

    Raises:
        ZUMOParseError: Various checks on annotations, categories, images

    Returns:
        zpy.saver.Saver: Saver object.
    """
    log.info(f'Parsing ZUMO annotations at {annotation_file}...')

    # Check annotation file path
    annotation_file = zpy.files.verify_path(annotation_file)
    if data_dir is not None:
        data_dir = zpy.files.verify_path(data_dir, check_dir=True)
    else:
        # If no data_dir, assume annotation file is in the root folder.
        data_dir = annotation_file.parent

    zumo_metadata = zpy.files.read_json(annotation_file)
    images = zumo_metadata['images']
    if len(images.keys()) == 0:
        raise ZUMOParseError(f'no images found in {annotation_file}')
    categories = zumo_metadata['categories']
    if len(categories.keys()) == 0:
        raise ZUMOParseError(f'no categories found in {annotation_file}')
    annotations = zumo_metadata['annotations']
    if len(annotations) == 0:
        raise ZUMOParseError(
            f'no annotations found in {annotation_file}')
    log.info(
        f'images:{len(images)} categories:{len(categories)} annotations:{len(annotations)}')

    # Optionally output a saver object.
    if output_saver:
        saver = zpy.saver_image.ImageSaver(output_dir=data_dir,
                                           annotation_path=annotation_file,
                                           description=zumo_metadata['metadata']['description'],
                                           clean_dir=False,
                                           )

    # Check Images
    log.info('Parsing images...')
    img_ids = []
    for image_id, img in images.items():
        # HACK: JSON will convert int keys to str, so undo that here
        image_id = int(image_id)
        # Image ID
        if not image_id == img['id']:
            raise ZUMOParseError(
                f"image id {image_id} does not match image dict key {img['id']}")
        if not isinstance(image_id, int):
            raise ZUMOParseError(f'image id {image_id} must be int.')
        if image_id in img_ids:
            raise ZUMOParseError(f'image id {image_id} already used.')
        img_ids.append(image_id)
        if image_id < 0:
            raise ZUMOParseError(f'invalid image id {image_id}')
        # Frame
        frame = img.get('frame', None)
        if frame is not None:
            if not isinstance(frame, int):
                raise ZUMOParseError(f'frame {frame} must be int.')
            if image_id < 0:
                raise ZUMOParseError(f'invalid image frame {frame}')
        # Height and Width
        height, width = img['height'], img['width']
        if not isinstance(height, int):
            raise ZUMOParseError(f'height {height} must be int.')
        if not isinstance(width, int):
            raise ZUMOParseError(f'width {width} must be int.')
        if height <= 0 or width <= 0:
            raise ZUMOParseError(
                f'width and height h:{height} w:{width} must be > 0')
        # Name
        name = img.get('name', None)
        if name is not None:
            if not isinstance(name, str):
                raise ZUMOParseError(f'name {name} must be str.')
            if frame is not None and \
                (not zpy.files.id_from_image_name(name) == frame) and \
                    (not zpy.files.id_from_image_name(name) == image_id):
                raise ZUMOParseError(f'name {name} does not correspond to'
                                     f' frame {frame} or image_id {image_id}.')
        # Output path
        output_path = img.get('output_path', None)
        if output_path is not None:
            if not isinstance(output_path, str):
                raise ZUMOParseError(f'output_path {output_path} must be str.')
            if not Path(output_path).exists():
                raise ZUMOParseError(
                    f'output_path {output_path} does not exist')
        # Save each image to ImageSaver object
        if output_saver:
            saver.images[image_id] = img

    # Check Categories
    log.info('Parsing categories...')
    cat_ids = []
    cat_names = []
    for category_id, category in categories.items():
        # Category Name
        category_name = category['name']
        if not isinstance(category_name, str):
            raise ZUMOParseError(
                f'category_name {category_name} must be str.')
        if category_name in cat_names:
            raise ZUMOParseError(
                f'category_name {category_name} already used')
        cat_names.append(category_name)
        # HACK: JSON will convert int keys to str, so undo that here
        category_id = int(category_id)
        # Category ID
        if not category_id == category['id']:
            raise ZUMOParseError(
                f"category_id {category_id} does not match category dict key {category['id']}")
        if not isinstance(image_id, int):
            raise ZUMOParseError(
                f'category_id {category_id} must be int.')
        if category_id in cat_ids:
            raise ZUMOParseError(
                f'category id {category_id} already used')
        cat_ids.append(category_id)
        # Supercategories
        if category.get('supercategory', None) is not None:
            pass
        if category.get('supercategories', None) is not None:
            pass
        # Subcategories
        if category.get('subcategory', None) is not None:
            pass
        if category.get('subcategories', None) is not None:
            pass
        # Keypoints
        if category.get("keypoints", None) is not None:
            keypoints = category['keypoints']
            log.info(f"{len(keypoints)} keypoints:{keypoints}")
            if category.get('skeleton', None) is None:
                raise ZUMOParseError(
                    f'skeleton must be present with {keypoints}')
        # Save each category to ImageSaver object
        if output_saver:
            saver.categories[category_id] = category

    # Check Annotations
    log.info('Parsing annotations...')
    ann_ids = []
    for annotation in annotations:
        # IDs
        image_id, category_id, annotation_id = annotation[
            'image_id'], annotation['category_id'], annotation['id']
        if image_id not in img_ids:
            raise ZUMOParseError(
                f'annotation image id {image_id} not in {img_ids}')
        if category_id not in cat_ids:
            raise ZUMOParseError(
                f'annotation category id {category_id} not in {cat_ids}')
        if annotation_id in ann_ids:
            raise ZUMOParseError(
                f'annotation id {annotation_id} already used')
        ann_ids.append(annotation_id)

        # Bounding Boxes
        bbox = annotation.get('bbox', None)
        if bbox is not None:
            pass

        # Keypoints
        keypoints = annotation.get('num_keypoints', None)
        if keypoints is not None:
            if "keypoints_xyv" in annotation:
                if len(annotation["keypoints_xyv"]) != int(annotation["num_keypoints"])*3:
                    raise ZUMOParseError(
                        'keypoints_xyv not correct size {len(keypoints)}')
            if "keypoints_xyz" in annotation:
                if len(annotation["keypoints_xyz"]) != int(annotation["num_keypoints"])*3:
                    raise ZUMOParseError(
                        'keypoints_xyz not correct size {len(keypoints)}')

        # Save each annotation to ImageSaver object
        if output_saver:
            saver.annotations.append(annotation)

    if output_saver:
        return saver
    else:
        return None
