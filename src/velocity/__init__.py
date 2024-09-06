from ._config import config

__version__ = "0.0.0"

config.set("velocity:version", __version__)

__all__ = [
    config
]
