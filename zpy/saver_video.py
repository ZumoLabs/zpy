"""
    Video version of Saver object.
"""
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple, Union
from datetime import timedelta

import gin
import numpy as np

import zpy

log = logging.getLogger(__name__)


@gin.configurable
class VideoSaver(zpy.saver.Saver):
    """Holds the logic for saving video annotations at runtime."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.videos = {}
        self.video_name_to_id = {}

    @gin.configurable
    def add_video(self,
                  name: str = 'default video',
                  style: str = 'default',
                  output_path: Union[Path, str] = '/tmp/test.avi',
                  width: int = 640,
                  height: int = 480,
                  length: timedelta = 0,
                  zero_indexed: bool = True,
                  **kwargs,
                  ) -> Dict:
        """ Add a new annotation to the Saver object.

        Args:
            name (str, optional): Unique video name. Defaults to 'default video'.
            style (str, optional): Type of image in [default, segmenation, depth]. Defaults to 'default'.
            output_path (Union[Path, str], optional): Path to video file. Defaults to '/tmp/test.avi'.
            width (int, optional): Width of video frame. Defaults to 640.
            height (int, optional): Height of video frame. Defaults to 480.
            length (timedelta, optional): Length of video in seconds. Defaults to 0.
            zero_indexed (bool, optional): Whether video id is zero indexed. Defaults to True.

        Returns:
            Dict: The video annotation dictionary.
        """
        video = {
            'name': name,
            'style': style,
            'output_path': str(output_path),
            'relative_path': str(Path(output_path).relative_to(self.output_dir)),
            'width': width,
            'height': height,
            'length': length,
        }
        video.update(**kwargs)
        video['id'] = len(self.videos.keys())
        video['id'] += 0 if zero_indexed else 1
        log.debug(f'Adding video: {zpy.files.pretty_print(video)}')
        self.videos[video['id']] = video
        self.video_name_to_id[name] = video['id']
        return video

    @gin.configurable
    def add_annotation(self,
                       *args,
                       video: str = 'default video',
                       **kwargs,
                       ) -> Dict:
        """ Add a new annotation to the Saver object.

        Args:
            video (str, optional): Unique video name. Defaults to 'default video'.

        Returns:
            Dict: The annotation dictionary.
        """
        annotation = super().add_annotation(*args, **kwargs)
        video_id = self.video_name_to_id.get(video, None)
        assert video_id is not None, f'Could not find id for video {video}'
        annotation['video_id'] = video_id
        annotation.update(**kwargs)
        self.annotations.append(annotation)
        return annotation

    @gin.configurable
    def output_meta_analysis(self):
        """ Perform a full meta analysis, outputting some meta files. """
        # TODO: implement meta-analysis for video datasets
        pass
