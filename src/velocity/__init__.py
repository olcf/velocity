from loguru import logger; logger.disable("velocity")  # disable logging at the module level
from ._config import config


__all__ = [config]
