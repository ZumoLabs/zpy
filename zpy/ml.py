from typing import Dict
from cli.utils import auth_headers
from pathlib import Path
import json
import requests
import logging

experiment = None

log = logging.getLogger(__name__)


def init(
    name: str,
    sim: str,
    dataset: str,
    config: Dict,
    api_key: str,
    endpoint: str = 'https://ragnarok.zumok8s.org'
) -> None:
    """ Initialize a experiment run.

    Args:
        name (str): identifier for experiment
        sim (str. optional): identifier for simulation associated with experiment
        dataset (str, optional): identifier for dataset associated with experiment
        config (dict, optional): configuration details about experiment
        endpoint (str, optional): endpoint for updates
        
    Raises:
        idk
    """
    exp = Experiment(name=name, sim=sim, dataset=dataset, config=config, api_token=api_token)
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
    file = Path(file_path)
    file.resolve()
    exp._update(file_path=str(file), metrics=metrics)


class Experiment:
    """ experiment class for uploading """

    def __init__(
            self,
            name: str = None,
            sim: str = None,
            dataset: str = None,
            config: Dict = None,
            api_token: str = None,
            endpoint='https://ragnarok.zumok8s.org/api/v1/experiment'
        ) -> None:
        self.name = name
        self.sim = sim
        self.dataset = dataset
        self.config = config
        self.auth_headers = auth_headers(api_token)
        self.endpoint = endpoint

    def _post(data=None, files=None):
        """ post to endpoint """
        r = requests.post(self.endpoint, data=data, files=files, headers=self.auth_headers)
        if r.status_code == 201:
            log.info(f'created experiment : {self.name}')
        if r.status_code == 200:
            log.info(f'logged to experiment : {self.name}')
        else:
            log.warning(f'unable to update or create experiment : {self.name}')
        response = json.loads(r.text)
        log.debug('{r.status_code} : {response}')

    def _create(self):
        data = {'name': self.name}
        if sim:
            data['sim'] = self.sim
        if dataset:
            data['dataset'] = self.dataset
        if config:
            data['config'] = self.config
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
