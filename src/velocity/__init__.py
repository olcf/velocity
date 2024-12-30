from loguru import logger; logger.disable("velocity")   # noqa: E702 # disable logging at the module level
from ._config import config # noqa: E402


__all__ = [config]
