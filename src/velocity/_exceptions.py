"""Exceptions for velocity."""

from sys import stderr


class CannotFindDependency(Exception):
    """Cannot find an image dependency."""

    def __init__(self, *args) -> None:
        super().__init__(*args)


class NoAvailableBuild(Exception):
    """No available build can be found."""

    def __init__(self, *args) -> None:
        super().__init__(*args)


class EdgeViolatesDAG(Exception):
    """Edge breaks the DAG requirement of a graph."""

    def __init__(self, u_of_edge, v_of_edge, cycle) -> None:
        super().__init__(f"Addition of edge {u_of_edge} -> {v_of_edge} violates graph DAG requirement!")
        for c in cycle:
            print(f"{c[0]} -> {c[1]}", file=stderr)


class BackendNotSupported(Exception):
    """Container backend not supported."""

    def __init__(self, *args):
        super().__init__(*args)


class BackendNotAvailable(Exception):
    """Container backend not supported."""

    def __init__(self, *args):
        super().__init__(*args)


class UndefinedVariableInTemplate(Exception):
    """Undefined variable during substitution in template."""

    def __init__(self, *args):
        super().__init__(*args)


class RepeatedSection(Exception):
    """Repeated template section."""

    def __init__(self, *args):
        super().__init__(*args)


class LineOutsideOfSection(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class TemplateSyntaxError(Exception):
    def __init__(self, message, line: str = None):
        super().__init__(f"{message} {f':line: <{line}>' if line is not None else ''}")


class InvalidImageVersionError(Exception):
    """Invalid image version spec."""

    def __init__(self, *args):
        super().__init__(*args)


class InvalidConfigIdentifier(Exception):
    """Invalid configuration identifier."""

    def __init__(self, *args) -> None:
        super().__init__(*args)


class InvalidCLIArgumentFormat(Exception):
    """Invalid format for a CLI argument."""

    def __init__(self, *args) -> None:
        super().__init__(*args)
