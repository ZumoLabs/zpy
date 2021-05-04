"""
    COCO (Common Objects in Context) dataset format.
"""
import copy
import logging
from pathlib import Path
from typing import List, Union

import gin
import zpy

log = logging.getLogger(__name__)


class COCOParseError(Exception):
    """Invalid COCO Annotation found when parsing data contents."""

    pass


@gin.configurable
class OutputCOCO(zpy.output.Output):
    """Output class for COCO style annotations.

    https://cocodataset.org/#home

    """

    ANNOTATION_FILENAME = Path("_annotations.coco.json")

    def __init__(self, *args, **kwargs) -> Path:
        super().__init__(*args, annotation_filename=self.ANNOTATION_FILENAME, **kwargs)

    @gin.configurable
    def output_annotations(
        self,
        annotation_path: Union[Path, str] = None,
        splitseg: bool = False,
    ) -> Path:
        """Output COCO annotations to file.

        Args:
            annotation_path (Union[Path, str], optional): Output path for annotation file.
            splitseg (bool, optional): Optionally output split-segmentation annotations. Defaults to False.

        Returns:
            Path: Path to annotation file.
        """
        annotation_path = super().output_annotations(annotation_path=annotation_path)
        coco_dict = {
            "info": self.coco_info(),
            "licenses": self.coco_license(),
            "categories": self.coco_categories(),
            "images": self.coco_images(),
            "annotations": self.coco_annotations(),
        }
        # Write out annotations to file
        zpy.files.write_json(annotation_path, coco_dict)
        parse_coco_annotations(annotation_path, data_dir=self.saver.output_dir)
        # Output split-segmentation annotations
        if splitseg:
            log.info(
                "Outputting COCO annotations with multi-part"
                + "segmentation split into seperate annotations"
            )
            coco_dict["annotations"] = self.coco_split_segmentation_annotations()
            annotation_path = zpy.files.add_to_path(annotation_path, "splitseg")
            # Write out annotations to file
            zpy.files.write_json(annotation_path, coco_dict)
            parse_coco_annotations(annotation_path, data_dir=self.saver.output_dir)
        return annotation_path

    @gin.configurable
    def coco_info(self, keys_to_add: List[str] = None):
        """coco info"""
        coco_info = {
            "description": self.saver.metadata["description"],
            "url": self.saver.metadata["url"],
            "version": self.saver.metadata["date_created"],
            "year": self.saver.metadata["year"],
            "contributor": self.saver.metadata["contributor"],
            "date_created": self.saver.metadata["date_created"],
            "save_path": self.saver.metadata["save_path"],
        }
        # Add any extra keys.
        if keys_to_add is not None:
            for key in keys_to_add:
                value = self.saver.metadata.get(key, None)
                if value is not None:
                    coco_info[key] = value
        return coco_info

    def coco_license(self):
        """coco license"""
        return {
            "url": "http://zumolabs.ai/image_license/",
            "id": 0,
            "name": "Zumo Labs Image License",
        }

    @gin.configurable
    def coco_categories(
        self,
        keys_to_add: List[str] = [
            "keypoints",
            "skeleton",
            "supercategory",
            "subcategories",
        ],
    ):
        """coco categories"""
        coco_categories = []
        for category in self.saver.categories.values():
            coco_category = {
                "id": category["id"],
                "name": category["name"],
            }
            # Add any extra keys.
            if keys_to_add is not None:
                for key in keys_to_add:
                    value = category.get(key, None)
                    if value is not None:
                        coco_category[key] = value
            coco_categories.append(coco_category)
        return coco_categories

    @gin.configurable
    def coco_images(
        self,
        only_default_images: bool = True,
        keys_to_add: List[str] = None,
    ):
        """coco images"""
        coco_images = []
        for image in self.saver.images.values():
            if only_default_images and not image["style"] == "default":
                # COCO annotations only have image annotations
                # for RGB images. No segmentation images.
                continue
            coco_img = {
                "license": 0,
                "id": image["id"],
                "file_name": image["name"],
                "coco_url": image["name"],
                "width": image["width"],
                "height": image["height"],
                "date_captured": self.saver.metadata["date_created"],
                "flickr_url": ".",
            }
            # Add any extra keys.
            if keys_to_add is not None:
                for key in keys_to_add:
                    value = image.get(key, None)
                    if value is not None:
                        coco_img[key] = value
            coco_images.append(coco_img)
        return coco_images

    @gin.configurable
    def coco_annotations(
        self,
        keys_to_add: List[str] = ["bbox", "area", "segmentation"],
        clipped: bool = True,
        only_default_images: bool = True,
    ):
        """coco annotations"""
        coco_annotations = []
        for annotation in self.saver.annotations:
            if (
                only_default_images
                and not self.saver.images[annotation["image_id"]]["style"] == "default"
            ):
                # COCO annotations only have image annotations
                # for RGB images. No segmentation images.
                continue
            coco_ann = {
                "category_id": annotation["category_id"],
                "image_id": annotation["image_id"],
                "id": annotation["id"],
                "iscrowd": False,
            }
            if clipped:
                height = self.saver.images[annotation["image_id"]]["height"]
                width = self.saver.images[annotation["image_id"]]["width"]

            # Add any extra keys.
            if keys_to_add is not None:
                for key in keys_to_add:
                    value = annotation.get(key, None)
                    if value is not None:
                        if key == "segmentation":
                            coco_ann["segmentation"] = (
                                self.saver.clip_coordinate_list(
                                    width=width,
                                    height=height,
                                    annotation=annotation["segmentation"],
                                )
                                if clipped
                                else annotation["segmentation"]
                            )
                        elif key == "segmentation_rle":
                            coco_ann["segmentation_rle"] = annotation[
                                "segmentation_rle"
                            ]
                        elif key == "segmentation_float":
                            coco_ann["segmentation_float"] = (
                                self.saver.clip_coordinate_list(
                                    normalized=True,
                                    annotation=annotation["segmentation_float"],
                                )
                                if clipped
                                else annotation["segmentation_float"]
                            )
                        elif key == "bbox_float":
                            coco_ann["bbox_float"] = (
                                self.saver.clip_bbox(
                                    normalized=True, bbox=annotation["bbox_float"]
                                )
                                if clipped
                                else annotation["bbox_float"]
                            )
                        elif key == "bbox":
                            coco_ann["bbox"] = (
                                self.saver.clip_bbox(
                                    width=width, height=height, bbox=annotation["bbox"]
                                )
                                if clipped
                                else annotation["bbox"]
                            )
                        elif key == "bboxes_float":
                            coco_ann["bboxes_float"] = (
                                [
                                    self.saver.clip_bbox(normalized=True, bbox=bbox)
                                    for bbox in annotation["bboxes_float"]
                                ]
                                if clipped
                                else annotation["bboxes_float"]
                            )
                        elif key == "bboxes":
                            coco_ann["bboxes"] = (
                                [
                                    self.saver.clip_bbox(
                                        height=height, width=width, bbox=bbox
                                    )
                                    for bbox in annotation["bboxes"]
                                ]
                                if clipped
                                else annotation["bboxes"]
                            )
                        else:
                            coco_ann[key] = value
                    try:
                        if key == "area":
                            coco_ann["area"] = (
                                annotation["bbox"][2] * annotation["bbox"][3]
                            )
                        elif key == "areas":
                            coco_ann["areas"] = [
                                bbox[2] * bbox[3] for bbox in annotation["bboxes"]
                            ]
                    except Exception:
                        pass
            # HACK: Require bbox for an annotation
            if coco_ann.get("bbox", None) is not None:
                coco_annotations.append(coco_ann)

        return coco_annotations

    @gin.configurable
    def coco_split_segmentation_annotations(
        self,
        keys_to_add: List[str] = ["bbox", "area", "segmentation"],
        clipped: bool = True,
        only_default_images: bool = True,
    ):
        """coco annotations one per segmentation"""
        coco_annotations = []
        # Annotation id will be re-mapped
        annotation_id = 0
        for annotation in self.saver.annotations:
            if (
                only_default_images
                and not self.saver.images[annotation["image_id"]]["style"] == "default"
            ):
                # COCO annotations only have image annotations
                # for RGB images. No segmentation images.
                continue
            coco_ann = {
                "category_id": annotation["category_id"],
                "image_id": annotation["image_id"],
                "iscrowd": False,
            }
            if clipped:
                height = self.saver.images[annotation["image_id"]]["height"]
                width = self.saver.images[annotation["image_id"]]["width"]

            # Add any extra keys.
            if keys_to_add is not None:
                for key in keys_to_add:
                    value = annotation.get(key, None)
                    if value is not None:
                        coco_ann[key] = value

            # Annotations can be composed of multiple annotation components
            if annotation.get("segmentation") is not None:
                num_components = len(annotation["segmentation"])
            else:
                log.warning(
                    "Skipping annotation: split segmentation requires segmentaiton field."
                )
                continue

            # TODO: This can prolly be cleaned up?
            for i in range(num_components):
                _coco_ann = copy.deepcopy(coco_ann)
                try:
                    _coco_ann["segmentation"] = (
                        [
                            self.saver.clip_coordinate_list(
                                height=height,
                                width=width,
                                annotation=annotation["segmentation"][i],
                            )
                        ]
                        if clipped
                        else [annotation["segmentation"][i]]
                    )
                except Exception:
                    pass
                try:
                    _coco_ann["segmentation_rle"] = [annotation["segmentation_rle"][i]]
                except Exception:
                    pass
                try:
                    _coco_ann["segmentation_float"] = (
                        [
                            self.saver.clip_coordinate_list(
                                normalized=True,
                                annotation=annotation["segmentation_float"][i],
                            )
                        ]
                        if clipped
                        else [annotation["segmentation_float"][i]]
                    )
                except Exception:
                    pass
                try:
                    _coco_ann["bbox_float"] = (
                        self.saver.clip_bbox(
                            normalized=True, bbox=annotation["bboxes_float"][i]
                        )
                        if clipped
                        else annotation["bboxes_float"][i]
                    )
                except Exception:
                    pass
                try:
                    _coco_ann["bbox"] = (
                        self.saver.clip_bbox(
                            width=width, height=height, bbox=annotation["bboxes"][i]
                        )
                        if clipped
                        else annotation["bboxes"][i]
                    )
                except Exception:
                    pass
                try:
                    _coco_ann["area"] = annotation["areas"][i]
                except Exception:
                    pass

                # HACK: Require bbox for an annotation
                if _coco_ann.get("bbox", None) is not None:
                    _coco_ann["id"] = annotation_id
                    annotation_id += 1
                    coco_annotations.append(_coco_ann)

        return coco_annotations


@gin.configurable
def parse_coco_annotations(
    annotation_file: Union[Path, str],
    data_dir: Union[Path, str] = None,
    output_saver: bool = False,
    # Specify which keys to add to ImageSaver
    image_keys_to_add: List[str] = None,
) -> zpy.saver_image.ImageSaver:
    """Parse COCO annotations, optionally output a ImageSaver object.

    Args:
        annotation_file (Union[Path, str]): Path to annotation file.
        data_dir (Union[Path, str], optional): Directory containing data (images, video, etc).
        output_saver (bool, optional): Whether to return a Saver object or not. Defaults to False.
        image_keys_to_add (List[str], optional): Image dictionary keys to include when parsing COCO dict.

    Raises:
        COCOParseError: Various checks on annotations, categories, images

    Returns:
        zpy.saver_image.ImageSaver: Saver object for Image datasets.
    """
    log.info(f"Parsing COCO annotations at {annotation_file}...")
    # Check annotation file path
    annotation_file = zpy.files.verify_path(annotation_file)
    if data_dir is not None:
        data_dir = zpy.files.verify_path(data_dir, check_dir=True)
    else:
        # If no data_dir, assume annotation file is in the root folder.
        data_dir = annotation_file.parent

    # Check that categories, images, and annotations are not blank
    coco_annotations = zpy.files.read_json(annotation_file)
    images = coco_annotations["images"]
    if len(images) == 0:
        raise COCOParseError(f"no images found in {annotation_file}")
    categories = coco_annotations["categories"]
    if len(categories) == 0:
        raise COCOParseError(f"no categories found in {annotation_file}")
    annotations = coco_annotations["annotations"]
    if len(annotations) == 0:
        raise COCOParseError(f"no annotations found in {annotation_file}")
    log.info(
        f"images:{len(images)} categories:{len(categories)} annotations:{len(annotations)}"
    )

    # Optionally output a saver object.
    if output_saver:
        saver = zpy.saver_image.ImageSaver(
            output_dir=data_dir,
            annotation_path=annotation_file,
            description=coco_annotations["info"]["description"],
            clean_dir=False,
        )

    # Check Images
    log.info("Parsing images...")
    img_ids = []
    for img in images:
        # Image ID
        image_id = img["id"]
        if not isinstance(image_id, int):
            raise COCOParseError(f"image id {image_id} must be int.")
        if image_id in img_ids:
            raise COCOParseError(f"image id {image_id} already used.")
        img_ids.append(image_id)
        if image_id < 0:
            raise COCOParseError(f"invalid image id {image_id}")
        # Height and Width
        height, width = img["height"], img["width"]
        if not isinstance(height, int):
            raise COCOParseError(f"height {height} must be int.")
        if not isinstance(width, int):
            raise COCOParseError(f"width {width} must be int.")
        if height <= 0 or width <= 0:
            raise COCOParseError(f"width and height h:{height} w:{width} must be > 0")
        # Image Name
        filename = img["file_name"]
        if not isinstance(filename, str):
            raise COCOParseError(f"filename {filename} must be str.")
        image_path = data_dir / filename
        if not image_path.exists():
            raise COCOParseError(f"image path {image_path} does not exist")
        # COCO Path
        coco_url = img.get("coco_url", None)
        if coco_url is None:
            coco_url = filename
        coco_url = Path(coco_url)
        coco_path = data_dir / coco_url
        if not coco_path.exists():
            raise COCOParseError(f"coco url {coco_path} does not exist")
        # Save each image to ImageSaver object
        if output_saver:
            saver.images[image_id] = {
                "id": image_id,
                "name": filename,
                "output_path": str(coco_url),
                "height": height,
                "width": width,
                "style": "default",
            }
            # Add any extra keys.
            if image_keys_to_add is not None:
                for key in image_keys_to_add:
                    value = img.get(key, None)
                    if value is not None:
                        saver.images[image_id][key] = value

    # Check Categories
    log.info("Parsing categories...")
    cat_ids = []
    cat_names = []
    for category in categories:
        name, category_id = category["name"], category["id"]
        log.info(f"name:{name} id:{category_id}")
        # Category Name
        category_name = category["name"]
        if not isinstance(category_name, str):
            raise COCOParseError(f"category_name {category_name} must be str.")
        if category_name in cat_names:
            raise COCOParseError(f"category_name {category_name} already used")
        cat_names.append(category_name)
        # Category ID
        category_id = category["id"]
        if not isinstance(image_id, int):
            raise COCOParseError(f"category_id {category_id} must be int.")
        if category_id in cat_ids:
            raise COCOParseError(f"category id {category_id} already used")
        cat_ids.append(category_id)
        # Supercategories
        if category.get("supercategory", None) is not None:
            pass
        if category.get("supercategories", None) is not None:
            pass
        # Subcategories
        if category.get("subcategory", None) is not None:
            pass
        if category.get("subcategories", None) is not None:
            pass
        # Keypoints
        if category.get("keypoints", None) is not None:
            keypoints = category["keypoints"]
            log.info(f"{len(keypoints)} keypoints:{keypoints}")
            if category.get("skeleton", None) is None:
                raise COCOParseError(f"skeleton must be present with {keypoints}")
        # Save each category to ImageSaver object
        if output_saver:
            _category = saver.categories.get(category_id, None)
            if _category is None:
                saver.categories[category_id] = {}
            for key, value in category.items():
                saver.categories[category_id][key] = value

    # Check Annotations
    log.info("Parsing annotations...")
    ann_ids = []
    for annotation in annotations:
        # IDs
        image_id, category_id, annotation_id = (
            annotation["image_id"],
            annotation["category_id"],
            annotation["id"],
        )
        if image_id not in img_ids:
            raise COCOParseError(f"annotation img:{image_id} not in {img_ids}")
        if category_id not in cat_ids:
            raise COCOParseError(f"annotation cat:{category_id} not in {cat_ids}")
        if annotation_id in ann_ids:
            raise COCOParseError(f"annotation id:{annotation_id} already used")
        ann_ids.append(annotation_id)

        # Bounding Boxes
        bbox = annotation.get("bbox", None)
        if bbox is not None:
            pass

        # Keypoints
        keypoints = annotation.get("num_keypoints", None)
        if keypoints is not None:
            if "keypoints_xyv" in annotation:
                if (
                    len(annotation["keypoints_xyv"])
                    != int(annotation["num_keypoints"]) * 3
                ):
                    raise COCOParseError(
                        "keypoints_xyv not correct size {len(keypoints)}"
                    )
            if "keypoints_xyz" in annotation:
                if (
                    len(annotation["keypoints_xyz"])
                    != int(annotation["num_keypoints"]) * 3
                ):
                    raise COCOParseError(
                        "keypoints_xyz not correct size {len(keypoints)}"
                    )

        # Save each annotation to ImageSaver object
        if output_saver:
            saver.annotations.append(annotation)

    if output_saver:
        return saver
    else:
        return None
