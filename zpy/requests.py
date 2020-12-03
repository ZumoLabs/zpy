"""
    Utilities for multi-processing and requests.
"""
import json
import logging
import multiprocessing
import signal
import sys
import time
import traceback
from functools import partial, wraps
from pprint import pformat
from typing import Dict

import zmq

import gin
import zpy

log = logging.getLogger(__name__)


class InvalidRequest(Exception):
    """ Network message to launcher is incorrect. """
    pass


class Process(multiprocessing.Process):
    """ Allows bubbiling up exceptions from a python process. """

    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._pconn, self._cconn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            multiprocessing.Process.run(self)
            self._cconn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._cconn.send((e, tb))
            raise e

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception


def request_as_process(request_func):
    """ Decorator for running a request as a separate process. """
    @wraps(request_func)
    def wrapped_request_func(request: Dict) -> None:
        _reply = multiprocessing.Manager().dict()
        p = Process(target=request_func, args=(request, _reply))
        p.start()
        p.join()
        global reply
        reply.update(_reply)
        if p.exception:
            reply['exception'] = str(p.exception)
            reply['code'] = 400
    return wrapped_request_func


# Global signal variables (see func below)
abort = None
waiting = None
reply = None


def handle_signal(signum, frame) -> None:
    """ Handle interrupt signal. """
    log.info(f'Received interrupt signal {signum}')
    if waiting:
        sys.exit(1)
    global abort
    abort = True


def accept_requests(run_func):
    """ Decorator for accepting requests as seperate processes. """
    @wraps(run_func)
    def wrapped_run_func(bind_uri: str) -> None:
        """ Main entrypoint for request based communication. """
        log.info('Configuring zmq socket...')
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(bind_uri)
        signal.signal(signal.SIGTERM, handle_signal)
        global abort, waiting, reply
        abort = False
        while not abort:
            log.info('Waiting for requests...')
            waiting = True
            request = json.loads(socket.recv_json())
            log.info(f'Received request: {pformat(request)}')
            waiting = False

            # Reply will include duration of request
            start_time = time.time()
            try:
                # Make sure request type is valid
                request_type = request.get('type', None)
                if request_type is None:
                    raise InvalidRequest(f'Request missing field: type')
                if not isinstance(request_type, str):
                    raise InvalidRequest(
                        f'Request field type is not a string')

                # Request can set a log level
                log_level = request.get('log_level', None)
                if log_level is not None:
                    zpy.logging.set_log_levels()

                # Default reply will include a message and an error code
                reply = {
                    'request': request,
                    'code': 200,
                }

                # Reset any gin configs
                try:
                    gin.enter_interactive_mode()
                    gin.clear_config()
                except Exception as e:
                    log.warning(
                        f'Could not reset gin configs before request: {e}')

                # Call the function that was given
                run_func(request)

            except Exception as e:
                reply['error'] = str(e)
                reply['code'] = 400

            # Duration of request is logged and sent in reply
            duration = time.time() - start_time
            reply['duration'] = duration

            # Send reply message back through the socket
            zpy.logging.linebreaker_log('reply')
            log.info(f'{pformat(reply)}')
            socket.send_json(json.dumps(reply))

        log.info('Exiting launcher.')

    return wrapped_run_func
