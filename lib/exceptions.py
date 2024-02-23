from sys import stderr


class InvalidDependencySpecification(Exception):

    def __init__(self, spec, image, tag, file):
        super().__init__(f"The provided dependency '{spec}' for {image}@={tag} is invalid! Please fix {file}")


class NoAvailableBuild(Exception):

    def __init__(self, message):
        super().__init__(message)


class EdgeViolatesDAG(Exception):

    def __init__(self, u_of_edge, v_of_edge, cycle):
        super().__init__(f"Addition of edge {u_of_edge} -> {v_of_edge} violates graph DAG requirement!")
        for c in cycle:
            print(f'{c[0]} -> {c[1]}', file=stderr)


class BackendNotSupported(Exception):

    def __init__(self, backend):
        super().__init__(f"The '{backend}' is not supported!")


class UndefinedVariableInTemplate(Exception):

    def __init__(self, variable):
        super().__init__(f"The variable '{variable}' is undefined!")
