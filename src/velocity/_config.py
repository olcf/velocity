from loguru import logger
from ._exceptions import InvalidSchema, InvalidConfig
from platform import processor as arch
from pathlib import Path
from os import getlogin as os_getlogin

"""
Allowed schema configurations:

bool:
    required: bool=True
    default: bool

str:
    required: bool=True
    default: str
    allowed: list[str]=None     # None is treated as if there are no restrictions

list:
    required: bool=True
    default: list
    items: {schema}      # the types of items in the list (bool or str)

dict:
    required: bool=True
    auto: bool=False            # if not defined auto-generate
    cardinality: str="one"      # allowed values are 'one' or 'many'
                                # If many, the dict name is ignored and n matches of the dict are allowed
    properties: dict
"""

DEFAULT_BOOL_SCHEMA = {
    "type": bool,
}

DEFAULT_STR_SCHEMA = {
    "type": str,
}

DEFAULT_LIST_SCHEMA = {
    "type": list,
    "default": list(),
    "items": {
        "type": str,
        "required": False
    }
}

IM_SCHEMA = {
    "type": str,
    "default": "COMBINE",
    "allowed": ["COMBINE", "OVERRIDE"]
}

VELOCITY_SCHEMA = {
    "type": dict,
    "properties": {
        "velocity": {
            "type": dict,
            "properties": {
                "backend": DEFAULT_STR_SCHEMA,
                "distro:": DEFAULT_STR_SCHEMA,
                "system": DEFAULT_STR_SCHEMA,
                "verbose": {
                    "type": bool,
                    "default": False
                },
                "debug": {
                    "type": str,
                    "default": "INFO",
                    "allowed": ["INFO", "DEBUG"]
                }
            }
        },
        "build_specs": {
            "type": dict,
            "default": {
                "type": dict,
                "auto": True,
                "properties": {
                    "variables": DEFAULT_LIST_SCHEMA
                }
            },
            "system": {
                "type": dict,
                "required": False,
                "cardinality": "many",
                "properties": {
                    "default": {
                        "type": dict,
                        "auto": True,
                        "properties": {
                            "prolog_lines": DEFAULT_LIST_SCHEMA,
                            "IM_prolog_lines": IM_SCHEMA,
                            "variables": DEFAULT_LIST_SCHEMA,
                            "IM_variables": IM_SCHEMA
                        }
                    },
                    "backend": {
                        "type": dict,
                        "required": False,
                        "cardinality": "many",
                        "properties": {
                            "default": {
                                "type": dict,
                                "auto": True,
                                "properties": {
                                    "arguments": DEFAULT_LIST_SCHEMA,
                                    "IM_arguments": IM_SCHEMA,
                                    "prolog_lines": DEFAULT_LIST_SCHEMA,
                                    "IM_prolog_lines": IM_SCHEMA,
                                    "variables": DEFAULT_LIST_SCHEMA,
                                    "IM_variables": IM_SCHEMA
                                }
                            },
                            "image": {
                                "type": dict,
                                "required": False,
                                "cardinality": "many",
                                "properties": {
                                    "arguments": DEFAULT_LIST_SCHEMA,
                                    "IM_arguments": IM_SCHEMA,
                                    "dependencies": DEFAULT_LIST_SCHEMA,
                                    "IM_dependencies": IM_SCHEMA,
                                    "prolog_script": {
                                        "type": str,
                                        "default": None
                                    },
                                    "variables": DEFAULT_LIST_SCHEMA,
                                    "IM_variables": IM_SCHEMA
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


def validate_and_generate_config(config: dict | list | str | bool | None, schema: dict) -> bool:
    try:
        if schema["type"] == dict:
            allowed = {"type", "required", "auto", "cardinality", "properties"}
            if not allowed.issuperset(schema.keys()):
                raise InvalidSchema("schema {} contains invalid attributes: {}".format(
                    schema,
                    set(schema).difference(allowed)
                ))
            if not isinstance(schema["type"], type) or \
                    not isinstance(schema["required"], bool) or \
                    not isinstance(schema["auto"], bool) or \
                    schema["cardinality"] not in ("one", "many") or \
                    not (isinstance(schema["properties"], dict) and schema["properties"] is not None):
                raise InvalidSchema("schema {} contains invalid attribute types".format(
                    schema
                ))
            if not isinstance(config, dict) and config is not None:
                raise InvalidConfig("config type '{}' does not match schema type '{}'".format(
                    type(config),
                    schema["type"]
                ))

            if schema["required"]:
                if config is None:
                    raise InvalidConfig("schema required but config is '{}'".format(
                        None
                    ))
                else:
                    for p in config.keys():
                        for s in schema["properties"]:
                            validate_and_generate_config(config[p], s)
            else:
                if config is None:
                    return True


            # return True
        elif schema["type"] == list:
            pass
        elif schema["type"] == str:
            pass
        elif schema["type"] == bool:
            pass
        else:
            raise InvalidSchema("schema type '{}' is not valid".format(schema["type"]))

    except (KeyError, TypeError):
        logger.warning("schema {} is not a dict or does not specify type".format(schema))
    except (InvalidSchema, InvalidConfig) as e:
        logger.warning(e)
        return False


class Config:
    """Configuration class."""
    def __init__(self) -> None:
        self._config = dict()

    def set(self, item: str, value: int | bool | str | list | dict | None) -> None:
        """Set config property."""
        try:
            if item != "":
                parts: list[str] = item.split(":")
                set_value = self._config
                for p in parts:
                    if not p.isidentifier():
                        logger.warning("'{}' is not a valid identifier", format(item))
                    if p != parts[-1]:
                        if p not in set_value:
                            set_value[p] = dict()
                        set_value = set_value[p]
                    else:
                        set_value[p] = value
            else:
                raise AttributeError("you cannot set the base config node")
        except AttributeError as e:
            logger.warning(e)

    def get(self, item: str) -> int | bool | str | list | dict | None:
        """Get config property."""
        try:
            if item != "":
                parts: list[str] = item.split(":")
                ret_value = self._config
                for p in parts:
                    if not p.isidentifier():
                        logger.warning("'{}' is not a valid identifier", format(item))
                        return None
                    ret_value = ret_value[p]
                return ret_value
            else:
                return self._config
        except (KeyError, TypeError):
            logger.warning("could not find '{}' in config", format(item))
        return None

    def __str__(self) -> str:
        return str(self._config)


# default configuration
_config = Config()
_config.set("velocity", {
    "system": arch(),
    "backend": "apptainer",
    "distro": "ubuntu",
    "verbose": False,
    "debug": "WARNING",
    "config_dir": Path.home().joinpath(".velocity"),
    "build_dir": Path("/tmp").joinpath(os_getlogin(), "velocity")
})


# config singleton
config = _config
