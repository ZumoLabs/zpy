"""
    Logic for saving. 
"""

import copy
import logging
import os
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple, Union

import gin
import numpy as np
import zpy
import zpy.file

log = logging.getLogger(__name__)


@gin.configurable
class Saver:
    """Holds the logic for saving annotations at runtime."""

    # Names for annotation files, folders, configs, datasheets, etc
    HIDDEN_METAFOLDER_FILENAME = Path('.zumometa')
    HIDDEN_DATASHEET_FILENAME = Path('ZUMO_DATASHEET.txt')
    GIN_CONFIG_FILENAME = Path('config.gin')

    DATETIME_FORMAT = '20%y%m%d_%H%M%S'
    DATETIME_YEAR_FORMAT = '20%y'

    def __init__(self,
                 output_dir: Union[str, Path] = None,
                 annotation_path: Union[str, Path] = None,
                 description: str = 'Description of dataset.',
                 clean_dir: bool = True,
                 ):
        # the output dir
        if output_dir is None:
            output_dir = zpy.file.default_temp_path()
        self.output_dir = zpy.file.verify_path(
            output_dir, make=True, check_dir=True)
        log.debug(f'Saver output directory at {output_dir}')
        if clean_dir:
            zpy.file.clean_dir(self.output_dir)
        # Annotation files can be optionally written out to a different dir
        if annotation_path is None:
            self.annotation_path = annotation_path
        else:
            self.annotation_path = zpy.file.verify_path(annotation_path)
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
        self.images = {}
        self.categories = {}
        self.annotations = []
        # Reverse-lookup dictionaries for name/color to id
        self.category_name_to_id = {}
        self.image_name_to_id = {}
        self.seg_annotations_color_to_id = {}

    @gin.configurable
    def add_category(self,
                     name: str = 'default',
                     supercategories: List[str] = None,
                     subcategories: List[str] = None,
                     color:  Tuple[float] = (0., 0., 0.),
                     zero_indexed: bool = True,
                     **kwargs,
                     ) -> None:
        """ Add category. """
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
        log.debug(f'Adding category: {zpy.file.pretty_print(category)}')
        self.categories[category['id']] = category
        self.category_name_to_id[name] = category['id']

    @gin.configurable
    def remap_filter_categories(self,
                                category_remap: Dict = None,
                                ) -> None:
        """ Remap and filter category ids and names. """
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

    @gin.configurable
    def add_image(self,
                  name: str = 'default image',
                  style: str = 'default',
                  output_path: Union[str, Path] = '/tmp/test.png',
                  frame: int = 0,
                  width: int = 0,
                  height: int = 0,
                  zero_indexed: bool = True,
                  **kwargs,
                  ) -> None:
        """ Add image to save object. """
        image = {
            'name': name,
            'style': style,
            'output_path': str(output_path),
            'frame': frame,
            'width': width,
            'height': height,
        }
        image.update(**kwargs)
        image['id'] = len(self.images.keys())
        image['id'] += 0 if zero_indexed else 1
        log.debug(f'Adding image: {zpy.file.pretty_print(image)}')
        self.images[image['id']] = image
        self.image_name_to_id[name] = image['id']

    @gin.configurable
    def add_annotation(self,
                       image: str = 'default image',
                       category: str = None,
                       subcategory: str = None,
                       subcategory_zero_indexed: bool = True,
                       seg_image: str = None,
                       seg_color:  Tuple[float] = None,
                       parse_on_add: bool = True,
                       **kwargs,
                       ) -> None:
        """ Add annotation. """
        image_id = self.image_name_to_id.get(image, None)
        assert image_id is not None, f'Could not find id for image {image}'
        assert category is not None, 'Must provide a category for annotation.'
        category_id = self.category_name_to_id.get(category, None)
        assert category_id is not None, f'Could not find id for category {category}'
        self.categories[category_id]['count'] += 1
        annotation = {
            'image_id': image_id,
            'category_id': category_id,
        }
        if subcategory is not None:
            subcategory_id = self.categories[category_id]['subcategories'].index(
                subcategory)
            self.categories[category_id]['subcategory_count'][subcategory_id] += 1
            subcategory_id += 0 if subcategory_zero_indexed else 1
            annotation['subcategory_id'] = subcategory_id
        annotation.update(**kwargs)
        annotation['id'] = len(self.annotations)
        log.info(f'Adding annotation: {zpy.file.pretty_print(annotation)}')
        # For segmentation images, add bbox/poly/mask annotation
        if seg_image is not None and seg_color is not None:
            seg_image_id = self.image_name_to_id.get(seg_image, None)
            assert seg_image_id is not None, f'Could not find id for image {seg_image}'
            annotation['seg_color'] = seg_color
            if self.seg_annotations_color_to_id.get(seg_image, None) is None:
                self.seg_annotations_color_to_id[seg_image] = {}
            self.seg_annotations_color_to_id[seg_image][seg_color] = annotation['id']
        self.annotations.append(annotation)
        # This call creates correspondences between segmentation images
        # and the annotations. It should be used after both the images
        # and annotations have been added to the saver.
        if parse_on_add:
            self.parse_annotations_from_seg_image(image_name=seg_image)

    def parse_annotations_from_seg_image(self,
                                         image_name: str,
                                         ) -> Dict:
        """ Populate annotation field based on segmentation image. """
        # Verify that file is segmentation image
        is_iseg = zpy.file.file_is_of_type(
            image_name, 'instance segmentation image')
        is_cseg = zpy.file.file_is_of_type(
            image_name, 'class segmentation image')
        if not (is_iseg or is_cseg):
            raise ValueError('Image is not segmentation image')
        seg_image_id = self.image_name_to_id.get(image_name, None)
        assert seg_image_id is not None, f'Could not find id for image {image_name}'
        image_path = self.images[seg_image_id]['output_path']
        if self.seg_annotations_color_to_id.get(image_name, None) is None:
            log.warning(f'No annotations found for {image_name}')
        for annotation in zpy.image.seg_to_annotations(image_path):
            if self.seg_annotations_color_to_id[image_name].get(annotation['color'], None) is None:
                log.warning(
                    f'No annotations found for color {annotation["color"]} in {image_name}')
                log.warning(
                    f'Available colors are {list(self.seg_annotations_color_to_id[image_name].keys())}')
                closest_color = zpy.color.closest_color(
                    annotation["color"],
                    list(self.seg_annotations_color_to_id[image_name].keys()))
                if closest_color is None:
                    log.warning(
                        f'Could not find close enough color, skipping ...')
                    continue
                else:
                    log.warning(f'Using closest color {closest_color}')
                    idx = self.seg_annotations_color_to_id[image_name][closest_color]
            else:
                idx = self.seg_annotations_color_to_id[image_name][annotation["color"]]
            self.annotations[idx].update(annotation)

    def output_gin_config(self):
        """ Output the full gin config. """
        gin_config_filepath = self.output_dir / self.GIN_CONFIG_FILENAME
        log.info(f'Writing out gin config to {gin_config_filepath}')
        with open(gin_config_filepath, "w") as f:
            f.write(gin.operative_config_str())

    @gin.configurable
    def output_annotated_images(self,
                                num_annotated_images: int = 10,
                                ) -> None:
        """ Dump annotated sampled images to the meta folder. """
        log.info('Output annotated images...')
        import zpy.viz
        output_path = self.output_dir / self.HIDDEN_METAFOLDER_FILENAME
        output_path = zpy.file.verify_path(
            output_path, make=True, check_dir=True)
        for i, image in enumerate(self.images.values()):
            # Annotation images take a while
            if i >= num_annotated_images:
                return
            annotations = []
            for annotation in self.annotations:
                if annotation['image_id'] == image['id']:
                    annotations.append(annotation)
            if len(annotations) > 0:
                zpy.viz.draw_annotations(image_path=Path(image["output_path"]),
                                         annotations=annotations,
                                         categories=self.categories,
                                         output_path=output_path)

    @gin.configurable
    def output_meta_analysis(self,
                             image_sample_size: int = 50):
        """ Perform a full meta analysis.  """
        log.info(
            f'perform meta analysis image_sample_size:{image_sample_size}...')

        import zpy.file
        image_paths = [i['output_path']
                       for i in self.images.values() if i['style'] == 'default']
        image_paths = zpy.file.sample(
            image_paths, sample_size=image_sample_size)
        opened_images = [zpy.image.open_image(i) for i in image_paths]
        flat_images = zpy.image.flatten_images(opened_images)
        pixel_mean_std = zpy.image.pixel_mean_std(flat_images)

        meta_dict = {
            'number_images': len(self.images),
            'number_annotations': len(self.annotations),
            'number_categories': len(self.categories),
            'category_names': [c['name'] for c in self.categories.values()],
            'pixel_mean': np.array2string(pixel_mean_std["mean"], precision=2),
            'pixel_std': np.array2string(pixel_mean_std["std"], precision=2),
            'pixel_256_mean': np.array2string(pixel_mean_std["mean_256"], precision=0),
            'pixel_256_std': np.array2string(pixel_mean_std["std_256"], precision=0),
        }

        output_path = self.output_dir / self.HIDDEN_METAFOLDER_FILENAME
        output_path = zpy.file.verify_path(
            output_path, make=True, check_dir=True)
        self.write_datasheet(
            output_path / self.HIDDEN_DATASHEET_FILENAME, meta_dict)

        try:
            import zpy.viz
            zpy.viz.image_grid_plot(
                images=opened_images, output_path=output_path)
            zpy.viz.image_shape_plot(
                images=opened_images, output_path=output_path)
            zpy.viz.color_correlations_plot(
                flat_images=flat_images, output_path=output_path)
            zpy.viz.pixel_histograms(
                flat_images=flat_images, output_path=output_path)
            zpy.viz.category_barplot(
                categories=self.categories, output_path=output_path)
        except Exception as e:
            log.warning(f'Error when visualizing {e}')
            pass

    @staticmethod
    def write_datasheet(
        datasheet_path: str = None,
        info: Dict = None
    ) -> None:
        with datasheet_path.open('w') as f:
            for k, v in info.items():
                f.write(f'{k},{v}\n')

    @staticmethod
    def clip_annotation(
        height: int = None,
        width: int = None,
        is_float: bool = False,
        annotation: List[int] = None
    ) -> List[int]:
        if isinstance(annotation, list):
            return [self.clip_annotation(height=height,
                                         width=width,
                                         is_float=is_float,
                                         annotation=ann) for ann in annotation]
        new_annotation = []
        for x, y in zip(*[iter(annotation)]*2):
            new_x, new_y = x, y
            max_x, max_y = width, height
            if is_float:
                max_x, max_y = 1, 1
            if x > max_x:
                new_x = max_x
            if x < 0:
                new_x = 0
            if y > max_y:
                new_y = max_y
            if y < 0:
                new_y = 0
            new_annotation.append(new_x)
            new_annotation.append(new_y)
        return new_annotation
