"""Misc tools."""

from functools import wraps
from inspect import isfunction, stack, getmodulename
from loguru import logger
from re import fullmatch as re_fullmatch
from abc import ABCMeta


# this variable holds the current trace indent
current_trace_indent: list = [0, ]


def trace_function(_function):
    """Trace function calls. One thing to note is that all tracing before the logger is enabled
    in __main__.py will not get logged."""

    @wraps(_function)
    def wrapper(*args, **kwargs):
        """Internal trace function."""

        # check logging level. We know this is not recommended (https://github.com/Delgan/loguru/issues/402) but we
        # could not find another way to retrieve our log level. Importing ._config causes circular imports.
        if logger._core.min_level > 5:
            return _function(*args, **kwargs)

        # update call number
        wrapper.call_count = wrapper.call_count + 1

        # pre-call update indent
        current_trace_indent[0] = current_trace_indent[0] + 1

        # get caller info
        current_stack = stack()[1]
        calling_lineno: int = current_stack.lineno
        calling_module: str = "velocity.{}".format(getmodulename(current_stack.filename))

        # construct trace message (note: 'this_call_depth' will always be >= 1)
        depth_str: str = "|{}|".format(" " * (current_trace_indent[0] * 2))
        q_name_str: str = "function '{}:{} {}'".format(
            _function.__module__,
            _function.__code__.co_firstlineno,
            _function.__qualname__
        )
        call_number_str: str = "call #{} from {}:{} ".format(wrapper.call_count, calling_module, calling_lineno)
        argument_names: tuple[str] = _function.__code__.co_varnames[:_function.__code__.co_argcount]
        argument_str: str = ""
        for a in range(len(args)):
            if argument_names[a] == "self":
                argument_str += "self, "
            else:
                argument_str += "{}: {} ='{}', ".format(argument_names[a], type(args[a]).__name__, args[a])
        for a in argument_names:
            if a in kwargs:
                argument_str += "{}: {} ='{}', ".format(a, type(kwargs[a]).__name__, kwargs[a])
        argument_str = "with ({})".format(argument_str)
        argument_str = argument_str.replace("\x1b", "\\x1b")    # neutralize color escape sequences

        # log trace
        logger.trace("{} {} {} {}".format(depth_str, q_name_str, call_number_str, argument_str))

        # call _function
        result = _function(*args, **kwargs)

        # post-call update indent
        current_trace_indent[0] = current_trace_indent[0] - 1

        # return results of calling _function
        return result

    # set the wrapper call count
    wrapper.call_count = 0

    # return wrapped _function
    return wrapper


class OurMeta(type):
    """Metaclass to wrap class methods with @trace_function. We do not trace builtin functions
    in the form __\w+__ except for __init__."""
    def __new__(cls, *args, **kwargs):
        for name, value in args[2].items():
            if isfunction(value) and (not re_fullmatch(r"^__\w+__$", name) or name == "__init__"):
                args[2][name] = trace_function(args[2][name])
        return super().__new__(cls, args[0], args[1], args[2])


class OurABCMeta(ABCMeta):
    """Metaclass to wrap class methods with @trace_function and inherit from ABCMeta. We do not trace builtin
    functions in the form __\w+__ except for __init__."""
    def __new__(cls, *args, **kwargs):
        for name, value in args[2].items():
            if isfunction(value) and (not re_fullmatch(r"^__\w+__$", name) or name == "__init__"):
                args[2][name] = trace_function(args[2][name])
        return super().__new__(cls, args[0], args[1], args[2])
