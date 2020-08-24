"""
    Visualization utilities for tesseract.
    
    TODO: Match style of the data portal.
"""
from matplotlib.collections import PatchCollection
from matplotlib.patches import Arrow, Circle, Polygon, Rectangle
from matplotlib.ticker import MaxNLocator
from pathlib import Path
from typing import Dict, List, Tuple, Union
import logging
import matplotlib
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d as plt3d
import numpy as np
import os
import random
import time

import zpy
import zpy.file
import zpy.image
import zpy.color


log = logging.getLogger(__name__)


def pretty_axes(ax: matplotlib.axes.Axes) -> matplotlib.axes.Axes:
    """ Better looking matplotlib axes object. """
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().set_visible(False)
    ax.grid(axis='y', alpha=0.75)
    return ax


def plotter(func):
    """ Decorator for plotting images. """

    def wrapped(output_path: Union[str, Path] = None,
                show: bool = False,
                **kwargs,
                ) -> matplotlib.figure.Figure:
        output_path = zpy.file.verify_path(
            output_path, make=True, check_dir=True)
        plt.style.use('fivethirtyeight')
        plot_name, fig = func(**kwargs)
        if show:
            log.info(f'Displaying {plot_name}...')
            plt.show()
            time.sleep(1)
        output_path = output_path / (plot_name + '.png')
        plt.savefig(output_path, bbox_inches="tight", pad_inches=0)
        plt.close('all')
        return fig

    return wrapped


@plotter
def image_grid_plot(
        images: List[np.ndarray] = None,
        rows: int = 4,
        cols: int = 4,
) -> Tuple[str, matplotlib.figure.Figure]:
    """ Plots images in a grid. """
    assert images is not None, 'Images required.'
    sample_size = min(rows*cols, len(images))
    images = random.sample(images, sample_size)
    fig = plt.figure(figsize=(16, 16))
    plt.suptitle('Sample Images', fontsize=18)
    for n, image in enumerate(images):
        plt.subplot(rows, cols, n+1)
        plt.imshow(image)
        plt.grid(False)
        plt.xticks([])
        plt.yticks([])
    return 'image_grid_plot', fig


@plotter
def image_shape_plot(
    images: List[np.ndarray] = None,
) -> Tuple[str, matplotlib.figure.Figure]:
    """ Plots 2D histogram of the image shapes. """
    assert images is not None, 'Images required.'
    image_shapes = [np.shape(_) for _ in images]
    # HACK: Filter out 2D images
    image_shapes = [_ for _ in image_shapes if len(_) is 3]
    image_shape = np.asarray(image_shapes)
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.hist2d(image_shape[:, 0], image_shape[:, 1], bins=(50, 50))
    ax.set(title='Histogram of Image Sizes')
    ax.set(xlabel='Width in Pixels')
    ax.set(ylabel='Height in Pixels')
    # Pixel ticks should be integers
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    # locs, labels = plt.xticks()
    # plt.xticks(locs, [l.astype(int) for l in labels])
    # locs, labels = plt.yticks()
    # plt.yticks(locs, [l.astype(int) for l in labels])
    return 'image_shape_plot', fig


@plotter
def color_correlations_plot(
    flat_images: List[np.ndarray] = None,
) -> Tuple[str, matplotlib.figure.Figure]:
    """ Plots 2D histograms of color correlations: RG, RB, and BG. """
    assert flat_images is not None, 'Images required.'
    # HACK: Incorrect type assumption
    flat_images = flat_images[0]
    fig = plt.figure(figsize=(16, 5))
    plt.rcParams["axes.grid"] = False
    plt.suptitle('Pixel Color Correlations \n\n\n', fontsize=18)
    ax = plt.subplot(131)
    plt.hist2d(flat_images[:, 0], flat_images[:, 1],
               bins=(50, 50), density=True)
    plt.title('Red - Green', fontsize=16)
    ax = plt.subplot(132)
    plt.hist2d(flat_images[:, 0], flat_images[:, 2],
               bins=(50, 50), density=True)
    plt.title('Red - Blue', fontsize=16)
    ax = plt.subplot(133)
    plt.hist2d(flat_images[:, 1], flat_images[:, 2],
               bins=(50, 50), density=True)
    plt.title('Blue - Green', fontsize=16)
    return 'color_correlations_plot', fig


@plotter
def pixel_histograms(
    flat_images: List[np.ndarray] = None,
) -> Tuple[str, matplotlib.figure.Figure]:
    """ Plots histograms of pixel values for each color channel. """
    assert flat_images is not None, 'Images required.'
    import seaborn as sns
    # HACK: Incorrect type assumption
    flat_images = flat_images[0]
    fig = plt.figure(figsize=(16, 8))
    plt.suptitle('Pixel Histograms (Red, Green, Blue)', fontsize=18)
    ax = plt.subplot(311)
    ax = pretty_axes(ax)
    sns.distplot(flat_images[:, 0], bins=255, color='r', ax=ax)
    ax = plt.subplot(312)
    ax = pretty_axes(ax)
    sns.distplot(flat_images[:, 1], bins=255, color='g', ax=ax)
    ax = plt.subplot(313)
    ax = pretty_axes(ax)
    sns.distplot(flat_images[:, 2], bins=255, color='b', ax=ax)
    plt.tight_layout()
    return 'pixel_histograms', fig


@plotter
def category_barplot(
    categories: Dict[str, Dict] = None,
) -> Tuple[str, matplotlib.figure.Figure]:
    """ Histograms for categories and sub-categories. """
    assert categories is not None, 'categories required.'

    category_names = [c['name'] for c in categories.values()]
    category_count = [c['count'] for c in categories.values()]
    category_color = [c['color'] for c in categories.values()]
    num_categories = len(category_names)

    fig, ax = plt.subplots(figsize=(16, 6 * (num_categories + 1)))
    plt.rcParams["axes.grid"] = False

    # Category histograms
    subplot_num_rows = num_categories + 1
    subplot_num_cols = 1
    subplot_plot_idx = 1
    if num_categories >= 1:
        ax = plt.subplot(subplot_num_rows, subplot_num_cols, subplot_plot_idx)
        ax.barh(category_names, category_count, color=category_color)
        ax.set(title='Annotations per Category')
        ax.set(xlabel='Number of Annotations')
        ax.set(ylabel='Category Name')

    # Subcategory histograms
    for i, category in enumerate(categories.values()):
        subcategories = category['subcategories']
        if len(subcategories) > 1:
            ax = plt.subplot(subplot_num_rows,
                             subplot_num_cols,
                             subplot_plot_idx + i + 1)
            subcategory_count = category['subcategory_count']
            ax.barh(subcategories, category['subcategory_count'])
            ax.set(title=f'Annotations per Subcategory of {category["name"]}')
            ax.set(xlabel='Number of Annotations')
            ax.set(ylabel=f'Subcategory of {category["name"]}')
    return 'category_histograms', fig


@plotter
def draw_annotations(
    image_path: Union[str, Path] = None,
    annotations: List = None,
    categories: Dict[str, Dict] = None,
) -> None:
    """ Given an path to an image draw annotations. """
    log.info(f'draw annotations on {image_path}...')
    image = zpy.image.open_image(image_path)
    _, ax = plt.subplots()
    ax.imshow(image)
    for i, annotation in enumerate(annotations):
        log.debug(f'{i}: {annotation}')
        category_id = annotation['category_id']
        category_color = categories[category_id].get('color', None)
        if category_color is None:
            log.debug('Could not find category color, using random color instead.')
            category_color = zpy.color.random_color()
        if 'num_keypoints' in annotation:
            skeleton = categories[category_id]['skeleton']
            try:
                keypoints = annotation['keypoints_xyv']
            except KeyError:
                keypoints = annotation['keypoints']
            draw_keypoints(ax, keypoints, skeleton, 'r')
        # Only draw bounding box OR segmentation
        if 'segmentation' in annotation:
            draw_segmentation(ax, annotation['segmentation'], category_color)
        if 'bbox' in annotation:
            draw_bbox(ax, annotation['bbox'], category_color)
    plt.axis('off')
    fig = plt.gcf()
    DPI = fig.get_dpi()
    fig.set_size_inches(
        image.shape[1]/float(DPI),  # width
        image.shape[0]/float(DPI),  # height
    )
    full_name = f'{image_path.stem}_annotated'
    return full_name, fig


def draw_bbox(
        ax: matplotlib.axes.Axes,
        bbox: List,
        color: Tuple[int],
        alpha: float = 0.2) -> None:
    """ Draw a bounding box on the matplotlib axes object. """
    # TODO: fix the bordering in matplotlib so that the pixels
    #   line up appropriately bounding boxes are [x, y, w, h]
    log.debug(f'drawing bbox {bbox} {color}')
    r = Rectangle((bbox[0], bbox[1]),
                  (bbox[2]),
                  (bbox[3]),
                  linewidth=3,
                  color=color,
                  edgecolor=color,
                  alpha=alpha)
    ax.add_patch(r)


def draw_segmentation(
        ax: matplotlib.axes.Axes,
        segmentation: List,
        color: Tuple[int],
        alpha: float = 0.6) -> None:
    """ Draw a segmentation polygon on the matplotlib axes object. """
    log.debug(f'drawing segmentation {segmentation} {color}')
    for seg in segmentation:
        p = Polygon(
            np.array(seg).reshape((int(len(seg)/2), 2)),
            linewidth=3,
            color=color,
            alpha=alpha)
        ax.add_patch(p)


def draw_keypoints(
        ax: matplotlib.axes.Axes,
        keypoints: List,
        skeleton: Dict,
        color: Tuple[int],
        alpha: float = 0.8) -> None:
    """
    Draws keypoints of an instance and follows the rules for keypoint connections
    to draw lines between appropriate keypoints.

    "keypoints": [x1,y1,v1,...,xk,yk,vk]
    - Keypoint coordinates are floats measured from the top left image corner (and are 0-indexed).
    - We recommend rounding coordinates to the nearest pixel to reduce file size.
    - v indicates visibility
            v=0: not labeled (in which case x=y=0)
            v=1: labeled but not visible
            v=2: labeled and visible

    """
    for k1, k2 in skeleton:

        # HACK: 0 indexed versus 1 indexed skeleton
        if min(min(skeleton)) == 1:
            k1 -= 1
            k2 -= 1

        k1_x = keypoints[3*k1 + 0]
        k1_y = keypoints[3*k1 + 1]
        k1_v = keypoints[3*k1 + 2]

        k2_x = keypoints[3*k2 + 0]
        k2_y = keypoints[3*k2 + 1]
        k2_v = keypoints[3*k2 + 2]

        if k1_v == 1:
            circle = Circle(
                (k1_x, k1_y),
                radius=5,
                edgecolor=color,
                facecolor='w',
                alpha=alpha
            )
            ax.add_patch(circle)

        if k1_v == 2:
            circle = Circle(
                (k1_x, k1_y),
                radius=5,
                edgecolor=color,
                facecolor=color,
                alpha=alpha
            )
            ax.add_patch(circle)

        if k2_v == 1:
            circle = Circle(
                (k2_x, k2_y),
                radius=5,
                edgecolor=color,
                facecolor='w',
                alpha=alpha
            )
            ax.add_patch(circle)

        if k2_v == 2:
            circle = Circle(
                (k2_x, k2_y),
                radius=5,
                edgecolor=color,
                facecolor=color,
                alpha=alpha
            )
            ax.add_patch(circle)

        if k1_v != 0 and k2_v != 0:
            line = Arrow(
                k1_x,
                k1_y,
                k2_x-k1_x,
                k2_y-k1_y,
                color=color,
                alpha=alpha
            )
            ax.add_patch(line)


def draw_keypoints3D(
        ax: matplotlib.axes.Axes,
        keypoints_xyv: List,
        keypoints_xyz: List,
        skeleton: Dict,
        color: Tuple[int],
        alpha: float = 0.7) -> None:
    """
    Draws 3D keypoints of an instance and follows the rules for keypoint connections
    to draw lines between appropriate keypoints.
    """
    for k1, k2 in skeleton:

        # HACK: 0 indexed versus 1 indexed skeleton
        if min(min(skeleton)) == 1:
            k1 -= 1
            k2 -= 1

        k1_x = keypoints_xyv[3*k1 + 0]
        k1_y = keypoints_xyv[3*k1 + 1]
        k1_v = keypoints_xyv[3*k1 + 2]

        k2_x = keypoints_xyv[3*k2 + 0]
        k2_y = keypoints_xyv[3*k2 + 1]
        k2_v = keypoints_xyv[3*k2 + 2]

        k1_X = keypoints_xyz[3*k1 + 0]
        k1_Y = keypoints_xyz[3*k1 + 1]
        k1_Z = keypoints_xyz[3*k1 + 2]

        k2_X = keypoints_xyz[3*k2 + 0]
        k2_Y = keypoints_xyz[3*k2 + 1]
        k2_Z = keypoints_xyz[3*k2 + 2]

        if k1_v == 1:
            ax.scatter(
                k1_X, k1_Y, k1_Z,
                edgecolor=color,
                facecolor='w',
                alpha=alpha
            )

        if k1_v == 2:
            ax.scatter(
                k1_X, k1_Y, k1_Z,
                edgecolor=color,
                facecolor=color,
                alpha=alpha
            )

        if k2_v == 1:
            ax.scatter(
                k2_X, k2_Y, k2_Z,
                edgecolor=color,
                facecolor='w',
                alpha=alpha
            )

        if k2_v == 2:
            ax.scatter(
                k2_X, k2_Y, k2_Z,
                edgecolor=color,
                facecolor=color,
                alpha=alpha
            )

        if k1_v != 0 and k2_v != 0:

            xs = k1_X, k2_X
            ys = k1_Y, k2_Y
            zs = k1_Z, k2_Z
            line = plt3d.art3d.Line3D(
                xs, ys, zs,
                color=color,
                alpha=alpha)
            ax.add_line(line)


def threeD_plot() -> matplotlib.axes.Axes:
    """ Axes object for 3D matplotlib plot.

    TODO: UNUSED & DEPRECATED

    """
    fig = plt.figure()
    fig.set_size_inches(10, 10)
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(azim=120)
    return ax


def generate_video(
        path: Path,
        image_glob: str = 'IMG_%08d.png',
        output_file: str = 'out.mp4',
        fps: int = 30,
        overlay: Path = None) -> None:
    """ Generate a video from sequence of frames

    TODO: UNUSED & DEPRECATED

    """
    import ffmpeg
    image_regex = os.path.join(str(path), image_glob)
    cmd = ffmpeg.input(image_regex, framerate=fps)
    if overlay is not None:
        overlay_file = ffmpeg.input(overlay)
        cmd = cmd.overlay(
            overlay_file, x="(main_w-overlay_w-10)", y="(main_h-overlay_h-10)")
    cmd = cmd.output(output_file, pix_fmt='yuv420p')
    cmd.run()
