"""
    Code for training a model from the Detectron2 model zoo.
"""
from pathlib import Path
from typing import Dict
import logging
import os

import cv2
import numpy as np
import torch
import zpy
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.data.datasets import register_coco_instances
from detectron2.engine import DefaultPredictor, DefaultTrainer
from detectron2.evaluation import COCOEvaluator, DatasetEvaluators
from detectron2.structures import Instances
from detectron2.utils.visualizer import VisImage, Visualizer

log = logging.getLogger(__name__)

MODEL_CFGS = {
    "faster_rcnn_R_50_C4_1x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_R_50_C4_1x.yaml",
    "faster_rcnn_R_50_C4_3x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_R_50_C4_3x.yaml",
    "faster_rcnn_R_101_C4_3x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_R_101_C4_3x.yaml",
    "faster_rcnn_R_50_DC5_1x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_R_50_DC5_1x.yaml",
    "faster_rcnn_R_50_DC5_3x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_R_50_DC5_3x.yaml",
    "faster_rcnn_R_101_DC5_3x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_R_101_DC5_3x.yaml",
    "faster_rcnn_R_50_FPN_1x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_R_50_FPN_1x.yaml",
    "faster_rcnn_R_50_FPN_3x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml",
    "faster_rcnn_R_101_FPN_3x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml",
    "faster_rcnn_X_101_32x8d_FPN_3x": "/detectron2_repo/configs/COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml",
    "retinanet_R_50_FPN_1x": "/detectron2_repo/configs/COCO-Detection/retinanet_R_50_FPN_1x.yaml",
    "retinanet_R_50_FPN_3x": "/detectron2_repo/configs/COCO-Detection/retinanet_R_50_FPN_3x.yaml",
    "retinanet_R_101_FPN_3x": "/detectron2_repo/configs/COCO-Detection/retinanet_R_101_FPN_3x.yaml",
    # Region Proposal Network (Only givees predictor(image)['proposals'])
    "rpn_R_50_C4_1x": "/detectron2_repo/configs/COCO-Detection/rpn_R_50_C4_1x.yaml",
    "rpn_R_50_FPN_1x": "/detectron2_repo/configs/COCO-Detection/rpn_R_50_FPN_1x.yaml",
}
MODEL_WEIGHTS = {
    "faster_rcnn_R_50_C4_1x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_R_50_C4_1x/137257644/model_final_721ade.pkl",
    "faster_rcnn_R_50_C4_3x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_R_50_C4_3x/137849393/model_final_f97cb7.pkl",
    "faster_rcnn_R_101_C4_3x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_R_101_C4_3x/138204752/model_final_298dad.pkl",
    "faster_rcnn_R_50_DC5_1x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_R_50_DC5_1x/137847829/model_final_51d356.pkl",
    "faster_rcnn_R_50_DC5_3x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_R_50_DC5_3x/137849425/model_final_68d202.pkl",
    "faster_rcnn_R_101_DC5_3x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_R_101_DC5_3x/138204841/model_final_3e0943.pkl",
    "faster_rcnn_R_50_FPN_1x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_R_50_FPN_1x/137257794/model_final_b275ba.pkl",
    "faster_rcnn_R_50_FPN_3x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_R_50_FPN_3x/137849458/model_final_280758.pkl",
    "faster_rcnn_R_101_FPN_3x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_R_101_FPN_3x/137851257/model_final_f6e8b1.pkl",
    "faster_rcnn_X_101_32x8d_FPN_3x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x/139173657/model_final_68b088.pkl",
    "retinanet_R_50_FPN_1x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/rpn_R_50_C4_1x/137258005/model_final_450694.pkl",
    "retinanet_R_50_FPN_3x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/retinanet_R_50_FPN_3x/190397829/model_final_5bd44e.pkl",
    "retinanet_R_101_FPN_3x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/retinanet_R_101_FPN_3x/190397697/model_final_971ab9.pkl",
    # Region Proposal Network (Only gives predictor(image)['proposals'])
    "rpn_R_50_C4_1x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/rpn_R_50_C4_1x/137258005/model_final_450694.pkl",
    "rpn_R_50_FPN_1x": "https://dl.fbaipublicfiles.com/detectron2/COCO-Detection/rpn_R_50_FPN_1x/137258492/model_final_02ce48.pkl",
}


class CustomEvaluator(COCOEvaluator):
    """ Custom COCO Evaluator. """

    def __init__(self, *args, result_name: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.result_name = result_name

    def evaluate(self, *args, **kwargs):
        results = super().evaluate(*args, **kwargs)
        return results


class CustomTrainer(DefaultTrainer):
    """ Custom trainer uses custom evaluator. """

    @classmethod
    def build_evaluator(cls, cfg, dataset_name, output_folder=None):
        return DatasetEvaluators(
            [
                CustomEvaluator(
                    dataset_name,
                    tasks=("bbox",),
                    distributed=True,
                    result_name=dataset_name,
                    output_dir=os.path.join(
                        cfg.OUTPUT_DIR, f"eval_{dataset_name}"),
                )
            ]
        )


def train(
    output_dir: str = "/tmp",
    train_name : str = None,
    train_annotation_file_path: str = None,
    train_image_dir_path: str = None,
    test_name : str = None,
    test_annotation_file_path: str = None,
    test_image_dir_path: str = None,
    model: str = "faster_rcnn_R_50_C4_1x",
    test_thresh: float = 0.3,
    iters: int = 2,
    lr: float = 0.001,
    batch_size: int = 2,
    class_dict: Dict = dict(),
    batch_size_head_per_img: int = 64,
    output_local_predictions: bool = True,
    num_loader_threads: int = 0,
) -> Dict:

    log.info("-----------------------------------------")
    log.info("           LOAD MODEL AND DATA           ")
    log.info("-----------------------------------------")

    # Detectron2 has a config object that keeps all hyperparameters
    cfg = get_cfg()

    # Train on the CPU, if a GPU is not available
    if torch.cuda.is_available():
        log.info("Using GPU")
        cfg.MODEL.DEVICE = "cuda"
        # Clear out any stale GPU memory
        torch.cuda.empty_cache()
    else:
        log.info("Using CPU")
        cfg.MODEL.DEVICE = "cpu"

    # Threads are used to load data quicker
    cfg.DATALOADER.NUM_WORKERS = num_loader_threads
    log.info(f"Using {cfg.DATALOADER.NUM_WORKERS} threads to load data.")

    # Clear any previously registered datasets
    DatasetCatalog.clear()

    # Training dataset will be synthetic data
    if train_name not in DatasetCatalog:
        register_coco_instances(
            train_name, {}, train_annotation_file_path, train_image_dir_path)

    # Testing dataset will be real data
    if test_name not in DatasetCatalog:
        register_coco_instances(
            test_name, {}, test_annotation_file_path, test_image_dir_path)

    # Keep a list of images for inference
    inference_image_paths = []
    for image in zpy.files.read_json(test_annotation_file_path)['images']:
        _path = Path(test_image_dir_path) / image['file_name']
        inference_image_paths.append(_path)

    # Predictions and logs will be put into output directory
    output_dir = zpy.files.verify_path(output_dir, make=True, check_dir=True)
    log.info(f"Output will be sent to {output_dir}")

    cfg.merge_from_file(MODEL_CFGS[model])
    cfg.OUTPUT_DIR = str(output_dir)
    cfg.DATASETS.TRAIN = [train_name]
    cfg.DATASETS.TEST = [test_name]
    cfg.SOLVER.BASE_LR = lr
    cfg.MODEL.WEIGHTS = MODEL_WEIGHTS[model]
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = len(class_dict)
    cfg.SOLVER.MAX_ITER = iters  # (iters)
    # Score threshold when testing
    try:
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = test_thresh
    except:
        pass
    try:
        cfg.MODEL.TENSOR_MASK.SCORE_THRESH_TEST = test_thresh
    except:
        pass
    try:
        cfg.MODEL.RETINANET.SCORE_THRESH_TEST = test_thresh
    except:
        pass
    try:
        cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = test_thresh
    except:
        pass

    cfg.SOLVER.IMS_PER_BATCH = batch_size
    log.info(f"Using a batch size of {cfg.SOLVER.IMS_PER_BATCH}.")

    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = batch_size_head_per_img
    log.info(
        f"Using a batch size of {cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE} for model head."
    )

    log.info(f"Loading model {model}")

    log.info("-----------------------------------------")
    log.info("                 TRAIN                   ")
    log.info("-----------------------------------------")
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    trainer = CustomTrainer(cfg)
    trainer.resume_or_load(resume=False)
    trainer.train()

    log.info("-----------------------------------------")
    log.info("                INFERENCE                ")
    log.info("-----------------------------------------")
    cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
    predictor = DefaultPredictor(cfg)

    output_dir = Path(output_dir) / "predictions"
    zpy.files.verify_path(output_dir, make=True)

    for image_file in inference_image_paths:
        img: np.ndarray = cv2.imread(str(image_file))
        try:
            output: Instances = predictor(img)["instances"]
        except:
            continue

        # Predictions from output
        pred_box_data = []
        num_predictions = output.scores.shape[0]
        for i in range(num_predictions):
            bbox = [
                float(_)
                for _ in [_ for _ in output.pred_boxes[i].to(torch.device("cpu"))][0]
            ]
            score = float(output.scores[i])
            class_id = int(output.pred_classes[i])
            _box_data = {
                "box_caption": "(%.3f)" % (score),
                "position": {
                    "minX": bbox[0],
                    "minY": bbox[1],
                    "maxX": bbox[2],
                    "maxY": bbox[3],
                },
                "class_id": class_id,
                "domain": "pixel",
                "scores": {"score": score},
            }
            pred_box_data.append(_box_data)

        # Output prediction images to local output directory
        if output_local_predictions:

            v = Visualizer(
                img[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TEST[0]), scale=1.0
            )
            result: VisImage = v.draw_instance_predictions(output.to("cpu"))
            result_image: np.ndarray = result.get_image()[:, :, ::-1]

            file_path = str(output_dir / image_file.name)
            cv2.imwrite(file_path, result_image)
    
    # Free up GPU memory
    del trainer
    del predictor
    del cfg
    torch.cuda.empty_cache()
