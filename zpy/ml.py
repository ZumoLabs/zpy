from typing import Dict
from cli.utils import auth_headers
from pathlib import Path
import json
import requests
import logging

experiment = None

logger = logging.getLogger('zpyml')


def init(
    name: str,
    api_key: str,
    sim: str = None,
    dataset: str = None,
    config: Dict = None,
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
        file = Path(file_path)
        file.resolve()
    if not isinstance(metrics, Dict):
        raise Exception('{metrics} must be of type dict')
    exp._update(file_path=str(file), metrics=metrics)


class Experiment:
    """ experiment class for uploading """

    def __init__(
            self,
            name: str = None,
            sim: str = None,
            dataset: str = None,
            config: Dict = None,
            api_key: str = None,
            endpoint='http://localhost:8000/api/v1/experiment/'
#            endpoint='https://ragnarok.zumok8s.org/api/v1/experiment/'
        ) -> None:
        self.name = name
        self.sim = sim
        self.dataset = dataset
        self.config = config
        self.auth_headers = auth_headers(api_key)
        self.endpoint = endpoint

    def _post(self, data=None, files=None):
        """ post to endpoint """
        r = requests.post(self.endpoint, data=data, files=files, headers=self.auth_headers)
        if r.status_code == 201:
            logger.info(f'created experiment : {self.name}')
        if r.status_code == 200:
            logger.info(f'logged to experiment : {self.name}')
        else:
            r.raise_for_status()
        response = json.loads(r.text)
        logger.debug('{r.status_code} : {response}')

    def _create(self):
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
            file_path: str = None,
            metrics: Dict = None
        ) -> None:
        data = { 'name': self.name }
        if metrics:
            data['metrics'] = metrics
        files = None
        if file_path:
            files = {'file': open(file_path, 'rb')}
        self._post(data=data, files=files)
