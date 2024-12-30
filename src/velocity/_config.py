"""Config organizer. Provides default config object for velocity."""

from loguru import logger
from platform import processor as arch
from pathlib import Path
from os import getenv
from getpass import getuser
from yaml import safe_load as yaml_safe_load
from ._exceptions import InvalidConfigIdentifier
from ._tools import OurMeta

class Config(metaclass=OurMeta):
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
                        raise InvalidConfigIdentifier("'{}' is not a valid identifier.".format(item))
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

    def get(self, item: str, warn_on_miss=True) -> int | bool | str | list | dict | None:
        """Get configuration property. Return None if not found"""
        try:
            if item != "":
                parts: list[str] = item.split(":")
                ret_value = self._config
                # make all config identifiers comply with python identifiers
                for p in parts:
                    if not p.isidentifier():
                        raise InvalidConfigIdentifier("'{}' is not a valid identifier.".format(item))
                    ret_value = ret_value[p]
                return ret_value
            else:
                return self._config
        except (KeyError, TypeError):
            if warn_on_miss:
                logger.warning("Could not find '{}' in config.", format(item))
            else:
                logger.info("Could not find '{}' in config.", format(item))
        except InvalidConfigIdentifier as e:
            logger.exception(e)
        return None

    def load(self) -> None:
        """Load configuration."""
        if self.get("velocity:config_dir") is None:
            self.set("velocity:config_dir", Path.home().joinpath(".velocity").__str__())
        config_dir = Path(self.get("velocity:config_dir"))
        try:
            with open(config_dir.joinpath("config.yaml"), "r") as fi:
                conf = yaml_safe_load(fi)
                for k in conf:
                    self.set(k, conf[k])
        except FileNotFoundError:
            logger.warning("Could not load configuration file from '{}'!".format(config_dir.joinpath("config.yaml")))

    def __str__(self) -> str:
        return str(self._config)


# default configuration & singleton
_config = Config()
if getenv("VELOCITY_CONFIG_DIR") is not None:
    _config.set("velocity:config_dir", getenv("VELOCITY_CONFIG_DIR"))
_config.load()

# get config from environment variables
if getenv("VELOCITY_SYSTEM") is not None:
    _config.set("velocity:system", getenv("VELOCITY_SYSTEM"))

if getenv("VELOCITY_BACKEND") is not None:
    _config.set("velocity:backend", getenv("VELOCITY_BACKEND"))

if getenv("VELOCITY_DISTRO") is not None:
    _config.set("velocity:distro", getenv("VELOCITY_DISTRO"))

if getenv("VELOCITY_IMAGE_PATH") is not None:
    _config.set("velocity:image_path", getenv("VELOCITY_IMAGE_PATH"))

if getenv("VELOCITY_BUILD_DIR") is not None:
    _config.set("velocity:build_dir", getenv("VELOCITY_BUILD_DIR"))

if getenv("VELOCITY_LOGGING_LEVEL") is not None:
    _config.set("velocity:logging:level", getenv("VELOCITY_LOGGING_LEVEL"))

# set defaults for un-configured items
if _config.get("velocity:system", warn_on_miss=False) is None:
    _config.set("velocity:system", arch())

if _config.get("velocity:backend", warn_on_miss=False) is None:
    _config.set("velocity:backend", "apptainer")

if _config.get("velocity:distro", warn_on_miss=False) is None:
    _config.set("velocity:distro", "ubuntu")

if _config.get("velocity:logging:level", warn_on_miss=False) is None:
    _config.set("velocity:logging:level", "WARNING")

if _config.get("velocity:image_path", warn_on_miss=False) is None:
    image_dir = Path.home().joinpath(".velocity", "images")
    image_dir.mkdir(parents=True, exist_ok=True)
    _config.set("velocity:image_path", image_dir.__str__())

if _config.get("velocity:build_dir", warn_on_miss=False) is None:
    _config.set("velocity:build_dir", Path("/tmp").joinpath(getuser(), "velocity").__str__())

# export
config = _config
