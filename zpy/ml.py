from typing import Dict, Union
from cli.utils import auth_headers
from pathlib import Path
import json
import requests
import logging

ENDPOINT = 'https://ragnarok.zumok8s.org/api/v1/experiment/'
experiment = None
logger = None

def init(
    name: str,
    sim: str = None,
    dataset: str = None,
    config: Dict = None,
    api_key: str = None,
) -> None:
    """ Initialize a experiment run.

    Args:
        name (str): identifier for experiment
        sim (str. optional): identifier for simulation associated with experiment
        dataset (str, optional): identifier for dataset associated with experiment
        config (dict, optional): configuration details about experiment
        api_key (str, required): api_key to auth with backend
    Returns:
        experiment object
    """
    if api_key is None:
        raise PermissionError('please input zpy api_key')
    global logger
    logger = logging.getLogger(__name__)
    exp = Experiment(name=name, sim=sim, dataset=dataset, config=config, api_key=api_key)
    global experiment
    experiment = exp
    exp._create()


def log(
    metrics: str = None,
    file_path: str = None,
) -> None:
    """ Log an update to experiment.

    Args:
        metrics (str, optional): free form dictionary of data to log
        file_path (str, optional): file path to upload

    Raises:
        FileNotFoundError: if file_path doesnt exist
    """
    global experiment
    exp = experiment
    if file_path:
        file_path = Path(file_path).resolve()
    exp._update(file_path=file_path, metrics=metrics)


class Experiment:
    """ experiment class for uploading """

    def __init__(
            self,
            name: str = None,
            sim: str = None,
            dataset: str = None,
            config: Dict = None,
            api_key: str = None
        ) -> None:
        """ Experiment Class for ragnarok upload.

        Args:
            name (str): identifier for experiment
            sim (str. optional): identifier for simulation associated with experiment
            dataset (str, optional): identifier for dataset associated with experiment
            config (dict, optional): configuration details about experiment
            api_key (str, required): api_key to auth with backend
        """
        self.name = name
        self.sim = sim
        self.dataset = dataset
        self.config = config
        self.auth_headers = auth_headers(api_key)
        self.id = None

    def _post(self, data=None):
        """ post to endpoint """
        r = requests.post(ENDPOINT, data=data, headers=self.auth_headers)
        if r.status_code != 201:
            logger.debug(f'{r.text}')
            r.raise_for_status()
        self.id = json.loads(r.text)['id']
        logger.debug(f'{r.status_code}: {r.text}')

    def _put(self, data=None, files=None):
        """ put to endpoint """
        r = requests.put(f'{ENDPOINT}{self.id}/', data=data, files=files, headers=self.auth_headers)
        if r.status_code != 200:
            logger.debug(f'{r.text}')
            r.raise_for_status()
        logger.debug(f'{r.status_code}: {r.text}')

    def _create(self):
        """ request to create experiment """
        data = {'name': self.name}
        if self.sim:
            data['sim_name'] = self.sim
        if self.dataset:
            data['data_set_name'] = self.dataset
        if self.config:
            data['config'] = json.dumps(self.config)
        self._post(data=data)

    def _update(
            self,
            file_path: Union[Path, str] = None,
            metrics: Dict = None
        ) -> None:
        """ request to update experiment """
        data = {'name': self.name}
        if metrics:
            data['metrics'] = json.dumps(metrics)
        files = None
        if file_path:
            files = {'file': open(file_path, 'rb')}
            data['file_name'] = Path(file_path).name
        self._put(data=data, files=files)
