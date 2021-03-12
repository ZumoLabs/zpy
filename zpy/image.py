"""
    Image utilties.
"""
import logging
import random
from itertools import groupby
from pathlib import Path
from typing import Dict, List, Union

import gin
import numpy as np
from scipy import ndimage as ndi
from shapely.geometry import MultiPolygon, Polygon
from skimage import color, exposure, img_as_uint, io, measure
from skimage.exposure import match_histograms
from skimage.morphology import binary_closing, binary_opening
from skimage.transform import resize

import zpy

log = logging.getLogger(__name__)


def open_image(
    image_path: Union[Path, str],
) -> np.ndarray:
    """ Open image from path to ndarray.

    Args:
        image_path (Union[Path, str]): Path to image.

    Returns:
        np.ndarray: Image as numpy array.
    """
    image_path = zpy.files.verify_path(image_path, make=False)
    img = None
    try:
        img = io.imread(image_path)
        if img.shape[2] > 3:
            log.debug('RGBA image detected!')
            img = img[:, :, :3]
        if img.max() > 2.0:
            img = np.divide(img, 255.0)
    except Exception as e:
        log.error(f'Error {e} when opening {image_path}')
    return img


def remove_alpha_channel(
    image_path: Union[Path, str]
) -> None:
    """ Remove the alpha channel in an image (overwrites image).

    Args:
        image_path (Union[Path, str]): Path to image.
    """
    img = open_image(image_path)
    io.imsave(image_path, img)
    log.info(f'Saving image with no alpha channel at {image_path}')


@gin.configurable
def jpeg_compression(
    image_path: Union[Path, str],
    quality : int = 40,    
) -> Path:
    """ Add jpeg compression to an image (overwrites image).

    Args:
        image_path (Union[Path, str]): Path to image.
        quality (int, optional): Compression quality. Defaults to 40.

    Returns:
        Path: Path to image.
    """
    image_path = zpy.files.verify_path(image_path, make=False)
    img = io.imread(image_path)
    # Make sure image is jpeg
    if not image_path.suffix == '.jpeg':
        image_path = image_path.with_suffix('.jpeg')
    io.imsave(image_path, arr=img, quality=quality)
    log.info(f'Saving compressed image at {image_path}')
    return image_path


@gin.configurable
def resize_image(
    image_path: Union[Path, str],
    width: int = 640,
    height: int = 480,
) -> Path:
    """ Resize an image (overwrites image).

    Args:
        image_path (Union[Path, str]): Path to image.
        width (int, optional): Width of image. Defaults to 640.
        height (int, optional): Height of image. Defaults to 480.

    Returns:
        Path: Path to image.
    """
    img = open_image(image_path)
    resized_img = resize(img, (height, width), anti_aliasing=True)
    io.imsave(image_path, resized_img)


def pixel_mean_std(
    flat_images: List[np.ndarray],
) -> Dict:
    """ Return the pixel mean and std from a flattened images array.

    Args:
        flat_images (List[np.ndarray]): Image pixels in a flattened array

    Returns:
        Dict: Pixel means and std as floats and integers (256) 
    """
    # HACK: Incorrect type assumption
    flat_images = flat_images[0]
    if np.amax(flat_images) > 1:
        std_256 = np.std(flat_images, axis=0)
        mean_256 = np.mean(flat_images, axis=0)
        std = std_256 / 256
        mean = mean_256 / 256
    else:
        std = np.std(flat_images, axis=0)
        mean = np.mean(flat_images, axis=0)
        std_256 = std * 256.0
        mean_256 = mean * 256.0
    return {
        "mean": mean,
        "std": std,
        "mean_256": mean_256,
        "std_256": std_256,
    }


def flatten_images(
    images: List[np.ndarray],
    max_pixels: int = 500000,
) -> List[np.ndarray]:
    """ Flatten a list of images in ndarray form.

    Args:
        images (List[np.ndarray]): List of images in ndarray form.
        max_pixels (int, optional): Maximum number of pixels in the flattened array. Defaults to 500000.

    Returns:
        List[np.ndarray]: List of flattened images.
    """
    flat_images = []
    for image in images:
        dims = np.shape(image)
        if len(dims) == 3:
            flat_images.append(np.reshape(
                image, (dims[0] * dims[1], dims[2])))
    flat_images = np.concatenate(flat_images, axis=0)
    subsample = flat_images[np.random.randint(flat_images.shape[0],
                                              size=max_pixels), :]
    return [subsample]


def pad_with(vector, pad_width, iaxis, kwargs):
    """ Pad a vector.

    https://numpy.org/doc/stable/reference/generated/numpy.pad.html
    """
    pad_value = kwargs.get('padder', 10)
    vector[:pad_width[0]] = pad_value
    vector[-pad_width[1]:] = pad_value


def binary_mask_to_rle(binary_mask) -> Dict:
    """ Converts a binary mask to a RLE (run-length-encoded) dictionary.

    https://stackoverflow.com/questions/49494337/encode-numpy-array-using-uncompressed-rle-for-coco-dataset
    """
    binary_mask = np.asfortranarray(binary_mask)
    rle = {'counts': [], 'size': list(binary_mask.shape)}
    counts = rle.get('counts')
    for i, (value, elements) in enumerate(groupby(binary_mask.ravel(order='F'))):
        if i == 0 and value == 1:
            counts.append(0)
        counts.append(len(list(elements)))
    return rle


@gin.configurable
def seg_to_annotations(
        image_path: Union[Path, str],
        remove_salt: bool = True,
        rle_segmentations: bool = False,
        float_annotations: bool = False,
        max_categories: int = 1000
) -> List[Dict]:
    """ Convert a segmentation image into bounding boxes and polygon segmentations.

    Args:
        image_path (Union[Path, str]): Path to image.
        remove_salt (bool, optional): Remove salt when calculating bounding box and polygons. Defaults to True.
        rle_segmentations (bool, optional): Include RLE polygons in annotation dictionaries. Defaults to False.
        float_annotations (bool, optional): Include float (0, 1) bboxes/polygons in annotation dictionaries. Defaults to False.
        max_categories (int, optional): Maximum number of categories allowed in an image. Defaults to 1000.

    Raises:
        ValueError: Too many categories (usually means segmentation image is not single colors)

    Returns:
        List[Dict]: List of annotation dictionaries.
    """
    log.info(f'Extracting annotations from segmentation: {image_path}')
    image_path = zpy.files.verify_path(image_path, make=False)
    img = open_image(image_path)
    img_height, img_width = img.shape[0], img.shape[1]
    # Unique colors represent each unique category
    unique_colors = np.unique(img.reshape(-1, img.shape[2]), axis=0)
    # Store bboxes, seg polygons, and area in annotations list
    annotations = []
    # Loop through each category
    if unique_colors.shape[0] > max_categories:
        raise ValueError(
            f'Over {max_categories} categories: {unique_colors.shape[0]}')
    for i in range(unique_colors.shape[0]):
        seg_color = unique_colors[i, :]
        log.debug(f'Unique color {seg_color}')
        if all(np.equal(seg_color, np.zeros(3))):
            log.debug('Color is background.')
            continue
        # Make an image mask for this category
        masked_image = img.copy()
        mask = (img != seg_color).any(axis=-1)
        masked_image[mask] = np.zeros(3)
        masked_image = color.rgb2gray(masked_image)
        if log.getEffectiveLevel() == logging.DEBUG:
            masked_image_name = str(
                image_path.stem) + f'_masked_{i}' + str(image_path.suffix)
            masked_image_path = image_path.parent / masked_image_name
            io.imsave(masked_image_path,
                      img_as_uint(exposure.rescale_intensity(masked_image)))
        if remove_salt:
            # Remove "salt"
            # https://scikit-image.org/docs/dev/api/skimage.morphology
            masked_image = binary_opening(masked_image)
            masked_image = binary_closing(masked_image)
        else:
            masked_image = binary_opening(masked_image)
        # HACK: Pad masked image so segmented objects that extend beyond
        #       image are properly contoured
        masked_image = np.pad(masked_image, 1, pad_with, padder=False)
        # RLE encoded segmentation from binary image
        if rle_segmentations:
            rle_segmentation = binary_mask_to_rle(masked_image)
        # Fill in the holes
        filled_masked_image = ndi.binary_fill_holes(masked_image)
        # Get countours for each blob
        contours = measure.find_contours(
            filled_masked_image, 0.01, positive_orientation='low')
        log.debug(
            f'found {len(contours)} contours for {seg_color} in {image_path}')
        # HACK: Sometimes all you get is salt for an image, in this case
        #       do not add any annotation for this category.
        if len(contours) == 0:
            continue
        segmentations = []
        segmentations_float = []
        bboxes = []
        bboxes_float = []
        areas = []
        areas_float = []
        polygons = []
        for contour in contours:
            # Flip from (row, col) representation to (x, y)
            # and subtract the padding pixel
            for j in range(len(contour)):
                row, col = contour[j]
                contour[j] = (col - 1, row - 1)
            # Make a polygon and simplify it
            poly = Polygon(contour)
            poly = poly.simplify(1.0, preserve_topology=True)
            polygons.append(poly)
            # Segmentation
            segmentation = np.array(poly.exterior.coords).ravel().tolist()
            segmentations.append(segmentation)
            segmentations_float.append([
                x/img_height if k % 2 == 0 else x/img_width for k, x in enumerate(segmentation)
            ])
            # Bounding boxes
            x, y, max_x, max_y = poly.bounds
            bbox = (x, y, max_x - x, max_y - y)
            bbox_float = [
                bbox[0] / img_width,
                bbox[1] / img_height,
                bbox[2] / img_width,
                bbox[3] / img_height,
            ]
            bboxes.append(bbox)
            bboxes_float.append(bbox_float)
            # Areas
            areas.append(poly.area)
            areas_float.append(poly.area / (img_width * img_height))
        # Combine the polygons to calculate the bounding box and area
        multi_poly = MultiPolygon(polygons)
        x, y, max_x, max_y = multi_poly.bounds
        bbox = (x, y, max_x - x, max_y - y)
        area = multi_poly.area
        bbox_float = [
            bbox[0] / img_width,
            bbox[1] / img_height,
            bbox[2] / img_width,
            bbox[3] / img_height,
        ]
        area_float = area / (img_width * img_height)
        annotation = {
            'color': tuple(seg_color),
            # COCO standards
            'segmentation': segmentations,
            'bbox': bbox,
            'area': area,
            # List of list versions
            'bboxes': bboxes,
            'areas': areas,
        }
        if rle_segmentations:
            annotation['segmentation_rle'] = rle_segmentation
        if float_annotations:
            annotation['segmentation_float'] = segmentations_float
            annotation['bbox_float'] = bbox_float
            annotation['area_float'] = area_float
            annotation['bboxes_float'] = bboxes_float
            annotation['areas_float'] = areas_float
        annotations.append(annotation)
    return annotations