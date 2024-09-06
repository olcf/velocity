"""Config organizer. Provides default config object for velocity."""

from loguru import logger
from ._exceptions import InvalidConfigIdentifier
from platform import processor as arch
from pathlib import Path
from os import getlogin as get_username


class Config:
    """Configuration class. Stores configuration as a dictionary."""

    def __init__(self) -> None:
        self._config = dict()

    def set(self, item: str, value: int | bool | str | list | dict | None) -> None:
        """Set configuration property."""
        try:
            # do not let user set the root node
            if item != "":
                parts: list[str] = item.split(":")
                set_value = self._config
                for p in parts:
                    # make all config identifiers comply with python identifiers
                    if not p.isidentifier():
                        raise InvalidConfigIdentifier(
                            "'{}' is not a valid identifier.".format(item)
                        )
                    # walk config tree until the final node is found
                    if p != parts[-1]:
                        if p not in set_value:
                            set_value[p] = dict()
                        set_value = set_value[p]
                    else:
                        set_value[p] = value
            else:
                raise AttributeError("You cannot set the root config node.")
        except (AttributeError, InvalidConfigIdentifier) as e:
            logger.exception(e)

    def get(self, item: str) -> int | bool | str | list | dict | None:
        """Get configuration property. Return None if not found"""
        try:
            if item != "":
                parts: list[str] = item.split(":")
                ret_value = self._config
                # make all config identifiers comply with python identifiers
                for p in parts:
                    if not p.isidentifier():
                        raise InvalidConfigIdentifier(
                            "'{}' is not a valid identifier.".format(item)
                        )
                    ret_value = ret_value[p]
                return ret_value
            else:
                return self._config
        except (KeyError, TypeError):
            logger.warning("Could not find '{}' in config.", format(item))
        except InvalidConfigIdentifier as e:
            logger.exception(e)
        return None

    def __str__(self) -> str:
        return str(self._config)


# default configuration & singleton
_config = Config()
_config.set(
    "velocity",
    {
        "system": arch(),
        "backend": "apptainer",
        "distro": "ubuntu",
        "verbose": False,
        "debug": "WARNING",
        "config_dir": Path.home().joinpath(".velocity", "config"),
        "image_dir": Path.home().joinpath(".velocity", "images"),
        "build_dir": Path("/tmp").joinpath(get_username(), "velocity"),
    },
)
config = _config
