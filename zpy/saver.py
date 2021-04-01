"""
    Base Saver object for storing annotations, categories, etc during sim runtime.
"""
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple, Union

import gin
import numpy as np

import zpy

log = logging.getLogger(__name__)


@gin.configurable
class Saver:
    """ Stores annotations and categories throughout a run script.

    Provides functions for some additional meta files.

    Raises:
        ValueError: Incorrect function arguments.

    Returns:
        Saver: The Saver object.
    """

    # Names for annotation files, folders, configs, datasheets, etc
    HIDDEN_METAFOLDER_FILENAME = Path('.zumometa')
    HIDDEN_DATASHEET_FILENAME = Path('ZUMO_DATASHEET.txt')
    GIN_CONFIG_FILENAME = Path('config.gin')

    DATETIME_FORMAT = '20%y%m%d_%H%M%S'
    DATETIME_YEAR_FORMAT = '20%y'

    def __init__(self,
                 output_dir: Union[Path, str] = None,
                 annotation_path: Union[Path, str] = None,
                 description: str = 'Description of dataset.',
                 clean_dir: bool = True,
                 ):
        """ Creates a Saver object.

        Args:
            output_dir (Union[Path, str], optional): Directory where files will be dumped.
            annotation_path (Union[Path, str], optional): Path where annotation file will be dumped.
            description (str, optional): A couple sentences describing the dataset. Defaults to 'Description of dataset.'.
            clean_dir (bool, optional): Whether to empty/clean the output directory on object creation. Defaults to True.
        """
        # the output dir
        if output_dir is None:
            output_dir = zpy.files.default_temp_path()
        self.output_dir = zpy.files.verify_path(
            output_dir, make=True, check_dir=True)
        log.debug(f'Saver output directory at {output_dir}')
        if clean_dir:
            zpy.files.clean_dir(self.output_dir)
        # Annotation files can be optionally written out to a different dir
        if annotation_path is None:
            self.annotation_path = annotation_path
        else:
            self.annotation_path = zpy.files.verify_path(annotation_path)
            log.debug(f'Saver annotation path at {annotation_path}')
        # Very similar keys to COCO-style
        self.metadata = {
            'description': description,
            'contributor': 'Zumo Labs',
            'url': 'zumolabs.ai',
            'year': date.today().strftime(self.DATETIME_YEAR_FORMAT),
            'date_created': date.today().strftime(self.DATETIME_FORMAT),
            'save_path': str(self.output_dir),
        }
        self.categories = {}
        self.annotations = []
        # Reverse-lookup dictionaries for name/color to id
        self.category_name_to_id = {}

    @gin.configurable
    def add_annotation(self,
                       category: str = None,
                       subcategory: str = None,
                       subcategory_zero_indexed: bool = True,
                       **kwargs,
                       ) -> Dict:
        """ Add a new annotation to the Saver object.

        Pass any additional keys you want in the annotation dict as kwargs.

        Args:
            category (str, optional): The category that this annotation belongs to. Defaults to None.
            subcategory (str, optional): The sub-category that this annotation belongs to. Defaults to None.
            subcategory_zero_indexed (bool, optional): Whether sub-categories are zero indexed. Defaults to True.

        Returns:
            Dict: The annotation dictionary.
        """
        annotation = {'id': len(self.annotations)}
        if category is not None:
            category_id = self.category_name_to_id.get(category, None)
            assert category_id is not None, f'Could not find id for category {category}'
            self.categories[category_id]['count'] += 1
            annotation['category_id'] = category_id
        if subcategory is not None:
            subcategory_id = self.categories[category_id]['subcategories'].index(
                subcategory)
            self.categories[category_id]['subcategory_count'][subcategory_id] += 1
            subcategory_id += 0 if subcategory_zero_indexed else 1
            annotation['subcategory_id'] = subcategory_id
        return annotation

    @gin.configurable
    def add_category(self,
                     name: str = 'default',
                     supercategories: List[str] = None,
                     subcategories: List[str] = None,
                     color:  Tuple[float] = (0., 0., 0.),
                     zero_indexed: bool = True,
                     **kwargs,
                     ) -> Dict:
        """ Add a new category (also known as classes) to the Saver object.

        Pass any additional keys you want in the category dict as kwargs.

        Args:
            name (str, optional): Name of the category. Defaults to 'default'.
            supercategories (List[str], optional): Names of any supercategories. Defaults to None.
            subcategories (List[str], optional): Names of any subcategories. Defaults to None.
            color (Tuple[float], optional): Color of the category in segmentation images. Defaults to (0., 0., 0.).
            zero_indexed (bool, optional): Whether categories are zero-indexed. Defaults to True.

        Returns:
            Dict: The category dictionary.
        """
        # Default for super- and sub- categories is empty list
        supercategories = supercategories or []
        subcategories = subcategories or []
        category = {
            'name': name,
            'supercategories': supercategories,
            'subcategories': subcategories,
            'color': color,
            'count': 0,
            'subcategory_count': [0] * len(subcategories),
        }
        category.update(**kwargs)
        category['id'] = len(self.categories.keys())
        category['id'] += 0 if zero_indexed else 1
        log.debug(f'Adding category: {zpy.files.pretty_print(category)}')
        self.categories[category['id']] = category
        self.category_name_to_id[name] = category['id']
        return category

    @gin.configurable
    def remap_filter_categories(self,
                                category_remap: Dict = None,
                                ) -> None:
        """Re-map the categories (name and id correspondence).

        This will also filter out any categories not in the category_remap dict.

        Args:
            category_remap (Dict, optional): Mapping of categorie names to id in {id : name}. Defaults to None.

        Raises:
            ValueError: Incorrect format for category remap dictionary.
        """
        if category_remap is None:
            log.warning(
                'Attempted to remap categories with no category remap.')
            return

        # Intermediate variables for organization
        category_remap_ids = []
        category_remap_name_to_id = {}
        category_remap_old_id_to_new_id = {}

        # Check for duplicates and typing
        for _id, _name in category_remap.items():
            try:
                _id = int(_id)
                _name = str(_name)
            except ValueError:
                raise ValueError('Category remap must be {int : string}')
            if _name in category_remap_name_to_id:
                raise ValueError(f'Duplicate category name in remap: {_name}')
            if _id in category_remap_ids:
                raise ValueError(f'Duplicate category id in remap: {_id}')
            category_remap_ids.append(_id)
            category_remap_name_to_id[_name] = _id

        # Make sure the category names all exist in current categories
        category_names = [c['name'] for c in self.categories.values()]
        for category_name in category_remap_name_to_id:
            assert category_name in category_names, \
                f'Could not find category {category_name} in dataset when remap-ing'

        # Go through all of the current categories
        new_categories = {}
        for old_id, category in self.categories.items():
            # Matching is done using the name
            if category['name'] in category_remap_name_to_id:
                new_id = category_remap_name_to_id[category['name']]
                category_remap_old_id_to_new_id[old_id] = new_id
                category['id'] = new_id
                new_categories[new_id] = category
        # Overwrite the old categories
        self.categories = new_categories

        # Go through all of the current annotations
        new_annotations = []
        # Replace the category_id in all annotations
        for annotation in self.annotations:
            if annotation['category_id'] in category_remap_old_id_to_new_id:
                new_id = category_remap_old_id_to_new_id[annotation['category_id']]
                annotation['category_id'] = new_id
                new_annotations.append(annotation)
        # Overwrite the old annotations
        self.annotations = new_annotations

    def output_gin_config(self):
        """ Output the full gin config. """
        gin_config_filepath = self.output_dir / self.GIN_CONFIG_FILENAME
        log.info(f'Writing out gin config to {gin_config_filepath}')
        with open(gin_config_filepath, "w") as f:
            f.write(gin.operative_config_str())

    @staticmethod
    def write_datasheet(
        datasheet_path: str = None,
        info: Dict = None
    ):
        """ Writes datasheet dict to file.

        Args:
            datasheet_path (str, optional): Path where datasheet will be written.
            info (Dict, optional): Information to include in datasheet.

        """
        with datasheet_path.open('w') as f:
            for k, v in info.items():
                f.write(f'{k},{v}\n')

    @staticmethod
    def clip_coordinate_list(
        annotation: List[Union[int, float]] = None,
        height: Union[int, float] = None,
        width: Union[int, float] = None,
        normalized: bool = False,
    ) -> List[Union[int, float]]:
        """ Clip a list of pixel coordinates (e.g. segmentation polygon).

        Args:
            annotation (List[Union[int, float]], optional): List of pixel coordinates.
            height (Union[int, float], optional): Height used for clipping.
            width (Union[int, float], optional): Width used for clipping.
            normalized (bool, optional): Whether coordinates are normalized (0, 1) or integer pixel values. Defaults to False.

        Returns:
            List[Union[int, float]]: Clipped list of pixel coordniates.
        """
        if any(isinstance(i, list) for i in annotation):
            return [zpy.saver.Saver.clip_coordinate_list(height=height,
                                                         width=width,
                                                         normalized=normalized,
                                                         annotation=ann) for ann in annotation]
        if normalized:
            # Coordinates are in (0, 1)
            max_x, max_y = 1.0, 1.0
        else:
            # Coordinates are w.r.t image height and width
            max_x, max_y = width, height
        new_annotation = []
        # TODO: This zip unpack here is unreadable
        for x, y in zip(*[iter(annotation)]*2):
            new_x, new_y = x, y
            if x < 0:
                new_x = 0
            if y < 0:
                new_y = 0
            if x > max_x:
                new_x = max_x
            if y > max_y:
                new_y = max_y
            new_annotation.append(new_x)
            new_annotation.append(new_y)
        return new_annotation

    @staticmethod
    def clip_bbox(
        bbox: List[Union[int, float]] = None,
        height: Union[int, float] = None,
        width: Union[int, float] = None,
        normalized: bool = False,
    ) -> List[Union[int, float]]:
        """ Clip a bounding box in [x, y, width, height] format.

        Args:
            bbox (List[Union[int, float]], optional): Bounding box in [x, y, width, height] format.
            height (Union[int, float], optional): Height used for clipping.
            width (Union[int, float], optional): Width used for clipping.
            normalized (bool, optional): Whether bounding box values are normalized (0, 1) or integer pixel values. Defaults to False.

        Returns:
            List[Union[int, float]]: Clipped bounding box in [x, y, width, height] format.
        """
        if normalized:
            # Coordinates are in (0, 1)
            max_x, max_y = 1.0, 1.0
        else:
            # Coordinates are w.r.t image height and width
            max_x, max_y = width, height
        new_bbox = [0] * 4
        new_bbox[0] = max(0, min(bbox[0], max_x))
        new_bbox[1] = max(0, min(bbox[1], max_y))
        new_bbox[2] = max(0, min(bbox[2], (max_x - new_bbox[0])))
        new_bbox[3] = max(0, min(bbox[3], (max_y - new_bbox[1])))
        return new_bbox
