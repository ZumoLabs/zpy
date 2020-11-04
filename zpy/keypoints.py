"""
    Human Keypoint Skeleton Formats.
"""
import logging

import bpy
import gin

import zpy

log = logging.getLogger(__name__)


@gin.configurable
class Keypoints:
    """ Functionality for Keypoints."""

    # COCO(From pycoco)
    COCO_NAMES = [
        "nose",
        "left_eye", "right_eye",
        "left_ear", "right_ear",
        "left_shoulder", "right_shoulder",
        "left_elbow", "right_elbow",
        "left_wrist", "right_wrist",
        "left_hip", "right_hip",
        "left_knee", "right_knee",
        "left_ankle", "right_ankle"
    ]
    COCO_CONNECTIVITY = [[16, 14], [14, 12], [17, 15], [15, 13],
                         [12, 13], [6, 12], [7, 13], [6, 7],
                         [6, 8], [7, 9], [8, 10], [9, 11],
                         [2, 3], [1, 2], [1, 3], [2, 4],
                         [3, 5], [4, 6], [5, 7]]
    COCO_BONE_LOOKUP_MIXAMO = {
        "nose": "NoseEnd",
        "left_eye": "LeftEyeEnd",
        "right_eye": "RightEyeEnd",
        "left_ear": "LeftEarEnd",
        "right_ear": "RightEarEnd",
        "left_shoulder": "LeftArm",
        "right_shoulder": "RightArm",
        "left_elbow": "LeftForeArm",
        "right_elbow": "RightForeArm",
        "left_wrist": "LeftHand",
        "right_wrist": "RightHand",
        "left_hip": "LeftUpLeg",
        "right_hip": "RightUpLeg",
        "left_knee": "LeftLeg",
        "right_knee": "RightLeg",
        "left_ankle": "LeftFoot",
        "right_ankle": "RightFoot",
    }
    COCO_BONE_LOOKUP_ANIMA = {
        # TODO: Anima armature does not have eyes, ears, nose
        "nose": "Head",
        "left_eye": "Head",
        "right_eye": "Head",
        "left_ear": "Head",
        "right_ear": "Head",
        "left_shoulder": "LeftArm",
        "right_shoulder": "RightArm",
        "left_elbow": "LeftForeArm",
        "right_elbow": "RightForeArm",
        "left_wrist": "LeftHand",
        "right_wrist": "RightHand",
        "left_hip": "LeftUpLeg",
        "right_hip": "RightUpLeg",
        "left_knee": "LeftLeg",
        "right_knee": "RightLeg",
        "left_ankle": "LeftFoot",
        "right_ankle": "RightFoot",
    }

    # Body25B
    BODY25B_NAMES = [
        "Nose", "Neck",
        "RShoulder", "RElbow", "RWrist",
        "LShoulder", "LElbow", "LWrist",
        "RHip", "RKnee", "RAnkle",
        "LHip", "LKnee", "LAnkle",
        "REye", "LEye", "REar", "LEar",
    ]
    BODY25B_CONNECTIVITY = [[0, 1], [0, 2], [1, 3], [2, 4], [5, 7], [6, 8],
                            [7, 9], [8, 10], [5, 11], [6, 12], [11, 13],
                            [12, 14], [13, 15], [14, 16], [15, 19], [19, 20],
                            [15, 21], [16, 22], [22, 23], [16, 24],
                            [5, 17], [6, 17], [17, 18], [11, 12]]
    BODY25B_BONE_LOOKUP_MIXAMO = {
        "Nose": "NoseEnd",
        "Neck": "Head",
        "RShoulder": "RightShoulder",
        "RElbow": "RightForeArm",
        "RWrist": "RightHand",
        "LShoulder": "LeftShoulder",
        "LElbow": "LeftForeArm",
        "LWrist": "LeftHand",
        "RHip": "RightUpLeg",
        "RKnee": "RightLeg",
        "RAnkle": "RightFoot",
        "LHip": "LeftUpLeg",
        "LKnee": "LeftLeg",
        "LAnkle": "LeftFoot",
        "REye": "RightEyeEnd",
        "LEye": "LeftEyeEnd",
        "REar": "RightEarEnd",
        "LEar": "LeftEarEnd",
    }
    # TODO: Anima armature
    BODY25B_BONE_LOOKUP_ANIMA = {
        "Nose": "Head",
        "Neck": "Head",
        "RShoulder": "RightShoulder",
        "RElbow": "RightForeArm",
        "RWrist": "RightHand",
        "LShoulder": "LeftShoulder",
        "LElbow": "LeftForeArm",
        "LWrist": "LeftHand",
        "RHip": "RightUpLeg",
        "RKnee": "RightLeg",
        "RAnkle": "RightFoot",
        "LHip": "LeftUpLeg",
        "LKnee": "LeftLeg",
        "LAnkle": "LeftFoot",
        "REye": "RightEyeEnd",
        "LEye": "LeftEyeEnd",
        "REar": "RightEarEnd",
        "LEar": "LeftEarEnd",
    }

    def __init__(self,
                 root: bpy.types.Object,
                 style: str = 'coco',
                 armature: str = 'anima',
                 ):
        """ Initialize keypoint object. """
        if style == 'coco':
            self.names = self.COCO_NAMES
            self.connectivity = self.COCO_CONNECTIVITY
            if armature == 'mixamo':
                self.bone_lookup = self.COCO_BONE_LOOKUP_MIXAMO
            elif armature == 'anima':
                self.bone_lookup = self.COCO_BONE_LOOKUP_ANIMA
            else:
                raise ValueError(f'Unknown keypoint armature: {armature}')
        elif style == 'body25b':
            self.names = self.BODY25B_NAMES
            self.connectivity = self.BODY25B_CONNECTIVITY
            if armature == 'mixamo':
                self.bone_lookup = self.BODY25B_BONE_LOOKUP_MIXAMO
            elif armature == 'anima':
                self.bone_lookup = self.BODY25B_BONE_LOOKUP_ANIMA
            else:
                raise ValueError(f'Unknown keypoint armature: {armature}')
        else:
            raise ValueError(f'Unknown keypoint style: {style}')
        self.root = root
        self.style = style
        self.armature = armature
        self.bones = {bone.name: bone for bone in self.root.pose.bones}
        self.num_keypoints = None
        self.keypoints_xyv = None
        self.keypoints_xyz = None

    def update(self,
               world_transform=None,
               ) -> None:
        """ Add a keypoint skeleton. """
        self.num_keypoints = 0
        self.keypoints_xyv = []
        self.keypoints_xyz = []
        for name, bone_name in self.bone_lookup.items():
            bone = self.bones.get(bone_name, None)
            if bone is None:
                log.warning(
                    f'Could not find keypoint bone {name} using {bone_name}')
            if world_transform is None:
                pos = self.root.matrix_world @ bone.head
            else:
                pos = world_transform @ self.root.matrix_world @ bone.head
            x, y, v = zpy.camera.camera_xyv(pos, obj=self.root)
            self.keypoints_xyv += [x, y, v]
            self.keypoints_xyz += tuple(pos)
            self.num_keypoints += 1
