"""
    Gin-config utilities.
"""
import logging
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, Tuple, Union

import gin
import zpy

log = logging.getLogger(__name__)


def replace_human_redable_kwargs(
    gin_bindings: Dict,
    human_conversion: Dict = {
        "seed": "zpy.blender.set_seed.seed",
        "output_dir": "zpy.saver.Saver.output_dir",
        "output_path": "zpy.saver.Saver.output_dir",
        "num_images": "zpy.blender.step.num_steps",
        "num_frames": "zpy.blender.step.num_steps",
    },
) -> Tuple[str, Any]:
    """[summary]

    Args:
        gin_bindings (Dict): Gin bindings dictionary {gin binding : value}.
        human_conversion (Dict, optional): Conversion from zpy keys to human-readable keys.

    Returns:
        Tuple[str, Any]: A single gin bindings.

    Yields:
        Iterator[Tuple[str, Any]]: New gin bindings.
    """
    log.info("Converting human readable bindings to gin...")
    for key, value in gin_bindings.items():
        if human_conversion.get(key, None) is not None:
            log.info(f"Converted {key} to {human_conversion[key]}")
            yield human_conversion[key], value
        else:
            yield key, value


def parse_gin_bindings(
    gin_bindings: Dict = None,
) -> None:
    """Parse any extra gin bindings to the config.

    Args:
        gin_bindings (Dict, optional): Gin bindings dictionary {gin binding : value}.
    """
    if gin_bindings is None:
        log.info("No additional gin bindings to parse")
    else:
        log.info(f"Parsing additional bindings: {pformat(gin_bindings)}")
        with gin.unlock_config():
            for key, value in replace_human_redable_kwargs(gin_bindings):
                try:
                    gin.bind_parameter(key, value)
                    _message = "BOUND  "
                except Exception:
                    _message = "IGNORED"
                log.info(f"{_message} - {key} : {value}")


def parse_gin_config(
    gin_config: str = None,
    gin_config_dir: Union[Path, str] = "$CONFIG",
) -> None:
    """Parse a gin config file by path.

    Args:
        gin_config (str, optional): Name of gin config.
        gin_config_dir (Union[Path, str], optional): Directory with gin configs.

    Raises:
        zpy.requests.InvalidRequest: Cannot find gin config at path.
    """
    if gin_config is None:
        log.info("No gin file to parse.")
    else:
        if not gin_config.endswith(".gin"):
            gin_config = gin_config + ".gin"
        gin_config_filename = Path(gin_config)
        gin_config_dir = zpy.files.verify_path(gin_config_dir, check_dir=True)
        gin_config_path = gin_config_dir / gin_config_filename
        log.info(f"Parsing gin config at {gin_config_path}")
        if not gin_config_path.exists():
            raise zpy.requests.InvalidRequest(
                f"Could not find gin config at {gin_config_path}"
            )
        gin.clear_config()
        gin.parse_config_file(str(gin_config_path))


def parse_gin_in_request(
    request: Dict,
) -> None:
    """Parse any gin related keys in a request dict.

    Args:
        request (Dict): Request dictionary (see zpy.requests).
    """
    zpy.gin.parse_gin_config(gin_config=request.get("gin_config", None))
    zpy.gin.parse_gin_bindings(gin_bindings=request.get("gin_bindings", None))
    gin.finalize()
