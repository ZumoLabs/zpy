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
                  output_path: Union[str, Path] = '/tmp/test.avi',
                  width: int = 0,
                  height: int = 0,
                  length: timedelta = 0,
                  zero_indexed: bool = True,
                  **kwargs,
                  ) -> Dict:
        """ Add image to save object. """
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
        """ Add annotation. """
        annotation = super().add_annotation(*args, **kwargs)
        video_id = self.video_name_to_id.get(video, None)
        assert video_id is not None, f'Could not find id for video {video}'
        annotation['video_id'] = video_id
        annotation.update(**kwargs)
        self.annotations.append(annotation)
        return annotation

    @gin.configurable
    def output_meta_analysis(self):
        """ Perform a full meta analysis.  """
        log.warning('TODO: implement meta-analysis for video datasets')
