"""
    Splitting a dataset into train, validate, and test.
"""
import copy
import json
import logging
import random
from datetime import date
from pathlib import Path
from typing import Dict, List, Union

import gin

import zpy
from zpy.output_coco import COCOParseError, OutputCOCO
from zpy.output_zumo import OutputZUMO, ZUMOParseError, parse_zumo_annotations
from zpy.saver_image import ImageSaver

log = logging.getLogger(__name__)


class TVTParseError(Exception):
    """ Invalid annotations or dataset format found when performing TVT. """
    pass


@gin.configurable
def batch_to_tvt(batches_path: List[Union[str, Path]] = None,
                 output_dir: Union[str, Path] = None,
                 dataset_name: str = None,
                 tvt_format: str = 'zumo',
                 split_val: float = 0.25,
                 split_test: float = 0.25,
                 category_remap: Dict = None,
                 output_annotated_images: bool = True,
                 output_meta_analysis: bool = True,
                 output_coco_annotations: bool = False,
                 ):
    """ Combine a set of batches into one dataset, which will then be split
    into train, validate, and test datasets.
    """
    log.info('Converting batch of datasets into one Train-Val-Test dataset.')
    # Make sure each path in the list of batches is a directory
    batches_path = [zpy.files.verify_path(
        p, check_dir=True) for p in batches_path]

    # There will be a root "dataset" directory in the output path
    output_dir = zpy.files.verify_path(output_dir, check_dir=True)
    dst_path = output_dir / dataset_name
    dst_path.mkdir(exist_ok=True, parents=True)

    # TODO: Generalize so that this can separate into arbitrary datasets
    dataset_names = ['train', 'val', 'test']

    # Make directories for train, val, and test
    dataset_dirs = {}
    _dataset_dir = dst_path / dataset_name
    for name in dataset_names:
        dataset_dirs[name] = zpy.files.make_underscore_path(
            _dataset_dir, name)
        dataset_dirs[name].mkdir(exist_ok=True, parents=True)

    if tvt_format == 'zumo':
        log.info('TVT will use ZUMO formatted datasets.')

        # There will be a single "annotations" dir in the root "dataset" dir
        annotations_dir = dst_path.joinpath('annotations')
        annotations_dir.mkdir(exist_ok=True, parents=True)

        # Make annotation files for train, val, and test
        annotation_paths = {}
        zumo_annotation_paths = {}
        _annotation_path = annotations_dir / (dataset_name + '.json')
        for name in dataset_names:
            annotation_paths[name] = zpy.files.make_underscore_path(
                _annotation_path, name)
            zumo_annotation_paths[name] = zpy.files.make_underscore_path(
                _annotation_path, name + '_zumo')

        zumo_to_tvt(batches_path,
                    train_dir=dataset_dirs['train'],
                    test_dir=dataset_dirs['test'],
                    val_dir=dataset_dirs['val'],
                    annotation_train_filename=zumo_annotation_paths['train'],
                    annotation_val_filename=zumo_annotation_paths['val'],
                    annotation_test_filename=zumo_annotation_paths['test'],
                    split_val=split_val,
                    split_test=split_test
                    )

        for name in dataset_names:
            # Parse ZUMO annotations
            try:
                saver = parse_zumo_annotations(
                    annotation_file=zumo_annotation_paths[name],
                    data_dir=dataset_dirs[name],
                    output_saver=True,
                )
                # Re-map categories
                if category_remap is not None:
                    saver.remap_filter_categories(category_remap)
                # Output images with annotations drawn on top
                if output_annotated_images:
                    saver.output_annotated_images()
                # Output meta analysis folder
                if output_meta_analysis:
                    saver.output_meta_analysis()
                # COCO annotations
                if output_coco_annotations:
                    OutputCOCO(saver).output_annotations(
                        annotation_path=annotation_paths[name])
            except ZUMOParseError as e:
                log.exception(f'ZUMOParseError error for tvt:{name}')
            except COCOParseError as e:
                log.exception(f'COCOParseError error for tvt:{name}')

    elif tvt_format == 'sequences':
        log.info('TVT will split each batch into test, train, and val.')

    else:
        raise ValueError(f'Invalid format for tvt: {tvt_format}')


@gin.configurable
def zumo_to_tvt(batches_path: Union[str, Path] = None,
                train_dir: Union[str, Path] = None,
                test_dir: Union[str, Path] = None,
                val_dir: Union[str, Path] = None,
                annotation_train_filename: Union[str, Path] = None,
                annotation_val_filename: Union[str, Path] = None,
                annotation_test_filename: Union[str, Path] = None,
                split_val: float = None,
                split_test: float = None,
                require_bbox: bool = True,
                require_segmentation: bool = True,
                require_keypoints: bool = False,
                category_zero_indexed: bool = True,
                subcategory_zero_indexed: bool = True,
                image_zero_indexed: bool = True,
                ):
    """ Parse coco annotations within a list of batches and output tvt """

    # Dictionaries which will eventually get written out to file as JSONs
    default_dict = {
        'metadata': [],
        'categories': {},
        'images': {},
        'annotations': [],
    }
    train_annotation_dict = copy.deepcopy(default_dict)
    val_annotation_dict = copy.deepcopy(default_dict)
    test_annotation_dict = copy.deepcopy(default_dict)

    # Category id is shared amongst train, valid, and test
    category_id_old_to_new = {}
    category_names_to_old_id = {}
    category_id = -1 if category_zero_indexed else 0

    # Image id is shared amongst all batches
    train_image_id = -1 if image_zero_indexed else 0
    val_image_id = -1 if image_zero_indexed else 0
    test_image_id = -1 if image_zero_indexed else 0

    # Annotation id is shared amongst all batches
    train_annotation_id = -1
    val_annotation_id = -1
    test_annotation_id = -1

    # Metadata will be shared between all datasets
    dataset_metadata = None

    # Loop through each batch
    for batch_id, batch_path in enumerate(batches_path):
        # Make sure path is directory to batch
        if not batch_path.is_dir():
            log.warning(f'{batch_path} is not a directory')
            continue

        # There should be a zumo annotation file in each path
        zumo_annotation_path = batch_path / OutputZUMO.ANNOTATION_FILENAME
        if not zumo_annotation_path.exists():
            log.warning(f'No ZUMO JSON found at {zumo_annotation_path}')
            continue
        zumo_annotation = zpy.files.read_json(zumo_annotation_path)

        # Set the metadata from the first dataset batch
        if batch_id == 0:
            dataset_metadata = zumo_annotation['metadata'].copy()
            # Update time to now
            dataset_metadata['year'] = \
                date.today().strftime(ImageSaver.DATETIME_YEAR_FORMAT)
            dataset_metadata['date_created'] = \
                date.today().strftime(ImageSaver.DATETIME_FORMAT)

        # Verify that all batches have the same metadata fields
        for field in ['description', 'contributor', 'url']:
            if not zumo_annotation['metadata'][field] == dataset_metadata[field]:
                raise TVTParseError(
                    f'Batch at {batch_path} has different metadata for {field} than the others.')

        # Paste info and licenses into train, valid, and test datasets
        train_annotation_dict['metadata'] = dataset_metadata
        train_annotation_dict['metadata']['save_path'] = str(train_dir)
        val_annotation_dict['metadata'] = dataset_metadata
        val_annotation_dict['metadata']['save_path'] = str(val_dir)
        test_annotation_dict['metadata'] = dataset_metadata
        test_annotation_dict['metadata']['save_path'] = str(test_dir)

        # Copy over new categories
        for old_category_id, category in zumo_annotation['categories'].items():

            # Make sure there aren't categories with different ids and names
            _name = category['name']
            if _name in category_names_to_old_id:
                log.debug(f'Skipping duplicate category {_name}')
                if not old_category_id == category_names_to_old_id[_name]:
                    raise TVTParseError(
                        f'Category {_name} has different ids in different batches.')
                continue
            category_names_to_old_id[_name] = old_category_id

            # Update the category_id
            category_id += 1
            category_id_old_to_new[int(old_category_id)] = category_id
            category['id'] = category_id

            # Clear the count and subcategory count
            category['count'] = 0
            if 'subcategory_count' in category:
                category['subcategory_count'] = [0] * len(category['subcategory_count'])

            # Add category to annotation dicts
            train_annotation_dict['categories'][category_id] = copy.deepcopy(category)
            val_annotation_dict['categories'][category_id] = copy.deepcopy(category)
            test_annotation_dict['categories'][category_id] = copy.deepcopy(category)

        # Get the total number of frames
        frames = set()
        for image in zumo_annotation['images'].values():
            frames.add(image['frame'])
        num_frames = len(frames)
        log.debug(f'There are {num_frames} frames in batch at {batch_path}')

        # Split all images into test and valid using random indices
        num_val_frames = int(split_val * num_frames)
        num_test_frames = int(split_test * num_frames)
        val_frames = set(random.sample(frames, num_val_frames))
        test_frames = set(random.sample(
            frames.difference(val_frames), num_test_frames))

        # Dict to convert old image ids to new image ids
        image_id_old_to_new = {}

        # Sort (and copy over) images, splitting into test and train
        for image in zumo_annotation['images'].values():

            # HACK: Only look at RGB (default) images
            if not image['style'] == 'default':
                continue

            # Check first if validation, then test, finally train.
            if image['frame'] in val_frames:
                val_image_id += 1
                # Copy image over to the correct directory
                _tvt_image_copy(
                    old_idx=image['frame'],
                    new_idx=val_image_id,
                    src_dir=batch_path,
                    dst_dir=val_dir,
                )
                # Correct image id
                image_id_old_to_new[int(image['id'])] = val_image_id
                image['id'] = val_image_id
                # Add output path and image name
                image['name'] = zpy.files.make_rgb_image_name(val_image_id)
                image['output_path'] = str(val_dir / image['name'])
                # Add to annotation image dict
                val_annotation_dict['images'][val_image_id] = copy.deepcopy(image)
            elif image['frame'] in test_frames:
                test_image_id += 1
                # Copy image over to the correct directory
                _tvt_image_copy(
                    old_idx=image['frame'],
                    new_idx=test_image_id,
                    src_dir=batch_path,
                    dst_dir=test_dir,
                )
                # Correct image id
                image_id_old_to_new[int(image['id'])] = test_image_id
                image['id'] = test_image_id
                # Add output path and image name
                image['name'] = zpy.files.make_rgb_image_name(test_image_id)
                image['output_path'] = str(test_dir / image['name'])
                # Add to annotation image dict
                test_annotation_dict['images'][test_image_id] = copy.deepcopy(image)
            else:
                train_image_id += 1
                # Copy image over to the correct directory
                _tvt_image_copy(
                    old_idx=image['frame'],
                    new_idx=train_image_id,
                    src_dir=batch_path,
                    dst_dir=train_dir,
                )
                # Correct image id
                image_id_old_to_new[int(image['id'])] = train_image_id
                image['id'] = train_image_id
                # Add output path and image name
                image['name'] = zpy.files.make_rgb_image_name(train_image_id)
                image['output_path'] = str(train_dir / image['name'])
                # Add to annotation image dict
                train_annotation_dict['images'][train_image_id] = copy.deepcopy(image)

        # Sort annotations into test and train depending on image id
        for annotation in zumo_annotation['annotations']:
            # Optionally require any annotations to have certain fields
            if require_bbox and annotation.get('bbox', None) is None:
                continue
            if require_keypoints and annotation.get('keypoints_xyv', None) is None:
                continue
            if require_segmentation and annotation.get('segmentation', None) is None:
                continue
            # HACK: Get frame from image list
            _frame = zumo_annotation['images'][str(annotation['image_id'])]['frame']
            if _frame in val_frames:
                val_annotation_id += 1
                a_id = val_annotation_id
                annotation_dict = val_annotation_dict
            elif _frame in test_frames:
                test_annotation_id += 1
                a_id = test_annotation_id
                annotation_dict = test_annotation_dict
            else:
                train_annotation_id += 1
                a_id = train_annotation_id 
                annotation_dict = train_annotation_dict

            category_id = category_id_old_to_new[annotation['category_id']]
            image_id = image_id_old_to_new[annotation['image_id']]
            annotation['id'] = a_id
            annotation['image_id'] = image_id
            annotation['category_id'] = category_id
            annotation_dict['annotations'].append(copy.deepcopy(annotation))

            # Fix the category counts
            annotation_dict['categories'][category_id]['count'] += 1
            if 'subcategory_id' in annotation:
                subcategory_id = annotation['subcategory_id']
                subcategory_id -= 0 if subcategory_zero_indexed else 1
                annotation_dict['categories'][category_id]['subcategory_count'][subcategory_id] += 1

    # Write Jsons to file
    zpy.files.write_json(annotation_train_filename, train_annotation_dict)
    zpy.files.write_json(annotation_val_filename, val_annotation_dict)
    zpy.files.write_json(annotation_test_filename, test_annotation_dict)


@gin.configurable
def _tvt_image_copy(old_idx: int = 0,
                    new_idx: int = 0,
                    src_dir: Union[str, Path] = None,
                    dst_dir: Union[str, Path] = None,
                    copy_iseg: bool = False,
                    copy_cseg: bool = False,
                    copy_depth: bool = False,
                    ) -> None:
    """ Copy over an image and it's segmentation images to a train,test,val directory.
    """
    # Copy over RGB image
    zpy.files.filecopy(
        src_dir=src_dir,
        dst_dir=dst_dir,
        src_name=zpy.files.make_rgb_image_name(old_idx),
        dst_name=zpy.files.make_rgb_image_name(new_idx),
    )
    # Copy over iseg image
    if copy_iseg:
        zpy.files.filecopy(
            src_dir=src_dir,
            dst_dir=dst_dir,
            src_name=zpy.files.make_iseg_image_name(old_idx),
            dst_name=zpy.files.make_iseg_image_name(new_idx),
        )
    # Copy over cseg image
    if copy_cseg:
        zpy.files.filecopy(
            src_dir=src_dir,
            dst_dir=dst_dir,
            src_name=zpy.files.make_cseg_image_name(old_idx),
            dst_name=zpy.files.make_cseg_image_name(new_idx),
        )
    # Copy over depth image
    if copy_depth:
        zpy.files.filecopy(
            src_dir=src_dir,
            dst_dir=dst_dir,
            src_name=zpy.files.make_depth_image_name(old_idx),
            dst_name=zpy.files.make_depth_image_name(new_idx),
        )
