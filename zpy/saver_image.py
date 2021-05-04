"""
    Image version of Saver object.
"""
import logging
from pathlib import Path
from typing import Dict, Tuple, Union

import gin
import numpy as np

import zpy

log = logging.getLogger(__name__)


@gin.configurable
class ImageSaver(zpy.saver.Saver):
    """Saver class for Image based datasets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.images = {}
        self.image_name_to_id = {}
        self.seg_annotations_color_to_id = {}

    @gin.configurable
    def add_image(
        self,
        name: str = "default image",
        style: str = "default",
        output_path: Union[Path, str] = "/tmp/test.png",
        frame: int = 0,
        width: int = 640,
        height: int = 480,
        zero_indexed: bool = True,
        **kwargs,
    ) -> Dict:
        """Add a new image annotation to the Saver object.

        Pass any additional keys you want in the image annotation dict as kwargs.

        Args:
            name (str, optional): Unique image name. Defaults to 'default image'.
            style (str, optional): Type of image in [default, segmenation, depth]. Defaults to 'default'.
            output_path (Union[Path, str], optional): Path to image file. Defaults to '/tmp/test.png'.
            frame (int, optional): Frame is used to link images taken at the same moment in time. Defaults to 0.
            width (int, optional): Width of image. Defaults to 640.
            height (int, optional): Height of image. Defaults to 480.
            zero_indexed (bool, optional): Whether image id is zero indexed. Defaults to True.

        Returns:
            Dict: The image annotation dictionary.
        """
        image = {
            "name": name,
            "style": style,
            "output_path": str(output_path),
            "relative_path": str(Path(output_path).relative_to(self.output_dir)),
            "frame": frame,
            "width": width,
            "height": height,
        }
        image.update(**kwargs)
        image["id"] = len(self.images.keys())
        image["id"] += 0 if zero_indexed else 1
        log.debug(f"Adding image: {zpy.files.pretty_print(image)}")
        self.images[image["id"]] = image
        self.image_name_to_id[name] = image["id"]
        return image

    @gin.configurable
    def add_annotation(
        self,
        image: str = "default image",
        category: str = None,
        subcategory: str = None,
        subcategory_zero_indexed: bool = True,
        seg_image: str = None,
        seg_color: Tuple[float] = None,
        parse_on_add: bool = True,
        **kwargs,
    ) -> Dict:
        """Add a new annotation to the Saver object.

        Pass any additional keys you want in the annotation dict as kwargs.

        Args:
            image (str, optional): Unique image name. Defaults to 'default image'.
            category (str, optional): Name of category. Defaults to None.
            subcategory (str, optional): Name of subcategory. Defaults to None.
            subcategory_zero_indexed (bool, optional): Whether subcategories are zero-indexed. Defaults to True.
            seg_image (str, optional): Name of segmentation image that corresponds to this image. Defaults to None.
            seg_color (Tuple[float], optional): Segmentation color of entity in this annotation. Defaults to None.
            parse_on_add (bool, optional): Calculate bounding box and polygons and populate segmenation fields.
                Defaults to True.

        Returns:
            Dict: The annotation dictionary.
        """
        image_id = self.image_name_to_id.get(image, None)
        assert image_id is not None, f"Could not find id for image {image}"
        assert category is not None, "Must provide a category for annotation."
        category_id = self.category_name_to_id.get(category, None)
        assert category_id is not None, f"Could not find id for category {category}"
        self.categories[category_id]["count"] += 1
        annotation = {
            "image_id": image_id,
            "category_id": category_id,
        }
        if subcategory is not None:
            subcategory_id = self.categories[category_id]["subcategories"].index(
                subcategory
            )
            self.categories[category_id]["subcategory_count"][subcategory_id] += 1
            subcategory_id += 0 if subcategory_zero_indexed else 1
            annotation["subcategory_id"] = subcategory_id
        annotation.update(**kwargs)
        annotation["id"] = len(self.annotations)
        log.info(f"Adding annotation: {zpy.files.pretty_print(annotation)}")
        # For segmentation images, add bbox/poly/mask annotation
        if seg_image is not None and seg_color is not None:
            seg_image_id = self.image_name_to_id.get(seg_image, None)
            assert seg_image_id is not None, f"Could not find id for image {seg_image}"
            annotation["seg_color"] = seg_color
            if self.seg_annotations_color_to_id.get(seg_image, None) is None:
                self.seg_annotations_color_to_id[seg_image] = {}
            self.seg_annotations_color_to_id[seg_image][seg_color] = annotation["id"]
        self.annotations.append(annotation)
        # This call creates correspondences between segmentation images
        # and the annotations. It should be used after both the images
        # and annotations have been added to the saver.
        if parse_on_add:
            self.parse_annotations_from_seg_image(image_name=seg_image)
        return annotation

    def parse_annotations_from_seg_image(
        self,
        image_name: str,
    ) -> None:
        """Populate annotation field based on segmentation image.

        Args:
            image_name (str): Name of image in which to put parse out segmentations.

        Raises:
            ValueError: Image is not a segmentation image.
        """
        # Verify that file is segmentation image
        is_iseg = zpy.files.file_is_of_type(image_name, "instance segmentation image")
        is_cseg = zpy.files.file_is_of_type(image_name, "class segmentation image")
        if not (is_iseg or is_cseg):
            raise ValueError("Image is not segmentation image")
        seg_image_id = self.image_name_to_id.get(image_name, None)
        assert seg_image_id is not None, f"Could not find id for image {image_name}"
        image_path = self.images[seg_image_id]["output_path"]
        if self.seg_annotations_color_to_id.get(image_name, None) is None:
            log.warning(f"No annotations found for {image_name}")
        for annotation in zpy.image.seg_to_annotations(image_path):
            if (
                self.seg_annotations_color_to_id[image_name].get(
                    annotation["color"], None
                )
                is None
            ):
                log.warning(
                    f'No annotations found for color {annotation["color"]} in {image_name}'
                )
                log.warning(
                    f"Available colors are {list(self.seg_annotations_color_to_id[image_name].keys())}"
                )
                closest_color = zpy.color.closest_color(
                    annotation["color"],
                    list(self.seg_annotations_color_to_id[image_name].keys()),
                )
                if closest_color is None:
                    log.warning("Could not find close enough color, skipping ...")
                    continue
                else:
                    log.warning(f"Using closest color {closest_color}")
                    idx = self.seg_annotations_color_to_id[image_name][closest_color]
            else:
                idx = self.seg_annotations_color_to_id[image_name][annotation["color"]]
            self.annotations[idx].update(annotation)

    @gin.configurable
    def output_annotated_images(
        self,
        num_annotated_images: int = 10,
    ) -> None:
        """Dump annotated sampled images to the meta folder.

        Args:
            num_annotated_images (int, optional): Number of annotation images to output. Defaults to 10.
        """
        log.info("Output annotated images...")
        import zpy.viz

        output_path = self.output_dir / self.HIDDEN_METAFOLDER_FILENAME
        output_path = zpy.files.verify_path(output_path, make=True, check_dir=True)
        for i, image in enumerate(self.images.values()):
            # Annotation images take a while
            if i >= num_annotated_images:
                return
            annotations = []
            for annotation in self.annotations:
                if annotation["image_id"] == image["id"]:
                    annotations.append(annotation)
            if len(annotations) > 0:
                zpy.viz.draw_annotations(
                    image_path=Path(image["output_path"]),
                    annotations=annotations,
                    categories=self.categories,
                    output_path=output_path,
                )

    @gin.configurable
    def output_meta_analysis(
        self,
        image_sample_size: int = 50,
    ) -> None:
        """Perform a full meta analysis, outputting some meta files.

        Args:
            image_sample_size (int, optional): How many images to sample for meta analysis. Defaults to 50.
        """
        log.info(f"perform meta analysis image_sample_size:{image_sample_size}...")

        import zpy.files

        image_paths = [
            i["output_path"] for i in self.images.values() if i["style"] == "default"
        ]
        image_paths = zpy.files.sample(image_paths, sample_size=image_sample_size)
        opened_images = [zpy.image.open_image(i) for i in image_paths]
        flat_images = zpy.image.flatten_images(opened_images)
        pixel_mean_std = zpy.image.pixel_mean_std(flat_images)

        meta_dict = {
            "number_images": len(self.images),
            "number_annotations": len(self.annotations),
            "number_categories": len(self.categories),
            "category_names": [c["name"] for c in self.categories.values()],
            "pixel_mean": np.array2string(pixel_mean_std["mean"], precision=2),
            "pixel_std": np.array2string(pixel_mean_std["std"], precision=2),
            "pixel_256_mean": np.array2string(pixel_mean_std["mean_256"], precision=0),
            "pixel_256_std": np.array2string(pixel_mean_std["std_256"], precision=0),
        }

        output_path = self.output_dir / self.HIDDEN_METAFOLDER_FILENAME
        output_path = zpy.files.verify_path(output_path, make=True, check_dir=True)
        self.write_datasheet(output_path / self.HIDDEN_DATASHEET_FILENAME, meta_dict)

        try:
            import zpy.viz

            zpy.viz.image_grid_plot(images=opened_images, output_path=output_path)
            zpy.viz.image_shape_plot(images=opened_images, output_path=output_path)
            zpy.viz.color_correlations_plot(
                flat_images=flat_images, output_path=output_path
            )
            zpy.viz.pixel_histograms(flat_images=flat_images, output_path=output_path)
            zpy.viz.category_barplot(
                categories=self.categories, output_path=output_path
            )
        except Exception as e:
            log.warning(f"Error when visualizing {e}")
            pass
