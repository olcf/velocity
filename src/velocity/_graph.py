"""Graph library and tools for dependency graph"""
from loguru import logger
from re import split as re_split, fullmatch as re_fullmatch, Match as ReMatch
from ._exceptions import (
    InvalidImageVersionError,
    InvalidDependencySpecification,
    EdgeViolatesDAG,
    NoAvailableBuild
)
from pathlib import Path
from hashlib import sha256
from typing_extensions import Self
from networkx import (
    DiGraph as nx_DiGraph,
    is_directed_acyclic_graph as nx_is_directed_acyclic_graph,
    find_cycle as nx_find_cycle,
    neighbors as nx_neighbors,
    has_path as nx_has_path
)
from yaml import safe_load as yaml_safe_load
from ._config import config
from copy import deepcopy
from enum import Enum

VERSION_REGEX = \
    r"^(?P<major>[0-9]+)(?:\.(?P<minor>[0-9]+)(:?\.(?P<patch>[0-9]+))?)?(?:-(?P<suffix>[a-zA-Z0-9]+))?$"


def get_permutations(idx: int, sets: list[list]):
    """
    Get all the possible permutations from a list of lists
    :param idx: recursion level
    :param sets: sets for permutation
    :return: permutations
    """
    permutations = list()
    if len(sets) == 0:
        pass
    elif idx == len(sets) - 1:
        for i in sets[idx]:
            permutations.append({i})
    else:
        for i in sets[idx]:
            sub_permutations = get_permutations(idx + 1, sets)
            for sub in sub_permutations:
                permutations.append(sub.union({i}))
    return permutations


class Version:
    """Version class for images."""
    def __init__(self, version_specifier: str) -> None:
        self.vs = version_specifier
        try:
            version_dict: dict = re_fullmatch(VERSION_REGEX, version_specifier).groupdict()
            self.major: int | None = int(version_dict['major']) if version_dict['major'] is not None else None
            self.minor: int | None = int(version_dict['minor']) if version_dict['minor'] is not None else None
            self.patch: int | None = int(version_dict['patch']) if version_dict['patch'] is not None else None
            self.suffix: str | None = str(version_dict['suffix']) if version_dict['suffix'] is not None else None
            logger.trace("Version: {}".format(self.__str__()))
        except AttributeError:
            self.major: int | None = None
            self.minor: int | None = None
            self.patch: int | None = None
            self.suffix: str | None = None
        except ValueError:
            logger.error("Could not parse version string: {}".format(version_specifier))
            exit(1)

    @property
    def vcs(self) -> str:
        """Version Comparison String"""
        return "{:#>9}.{:#>9}.{:#>9}.{:~<9}".format(
            self.major if self.major is not None else "#",
            self.minor if self.minor is not None else "#",
            self.patch if self.patch is not None else "#",
            self.suffix if self.suffix is not None else "~"
        )

    def preferred(self, other) -> bool:
        """Determine which version to prefer when two version are "equal" ex. 12.3 vs 12.3.0-rc1"""
        return self.vcs > other.vcs

    @property
    def _vcs_t(self) -> str:
        """Version Comparison String Truncated"""
        vl: int = 0
        if self.major is None:
            pass
        elif self.minor is None:
            vl = 9
        elif self.patch is None:
            vl = 19
        elif self.suffix is None:
            vl = 29
        else:
            vl = 39
        return self.vcs[:vl]

    @classmethod
    def _cut_vcses_to_size(cls, one: Self, two: Self) -> tuple[str, str]:
        """Cut vcses to the longest common length"""
        length: int = min(len(one._vcs_t), len(two._vcs_t))
        return one._vcs_t[:length], two._vcs_t[:length]

    def __eq__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"'>' not supported between instances of "
                            f"'{type(self).__name__}' and '{type(other).__name__}'")
        s_vcs, o_vcs = self._cut_vcses_to_size(self, other)
        return s_vcs == o_vcs

    def __ne__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"'>' not supported between instances of "
                            f"'{type(self).__name__}' and '{type(other).__name__}'")
        s_vcs, o_vcs = self._cut_vcses_to_size(self, other)
        return s_vcs != o_vcs

    def __gt__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"'>' not supported between instances of "
                            f"'{type(self).__name__}' and '{type(other).__name__}'")
        return self.vcs > other.vcs and not self.__eq__(other)

    def __ge__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"'>' not supported between instances of "
                            f"'{type(self).__name__}' and '{type(other).__name__}'")
        return self.vcs > other.vcs or self.__eq__(other)

    def __lt__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"'>' not supported between instances of "
                            f"'{type(self).__name__}' and '{type(other).__name__}'")
        return self.vcs < other.vcs and not self.__eq__(other)

    def __le__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(f"'>' not supported between instances of "
                            f"'{type(self).__name__}' and '{type(other).__name__}'")
        return self.vcs < other.vcs or self.__eq__(other)

    def __str__(self) -> str:
        return self.vs


class Spec:
    def __init__(self):
        pass


class Image:
    def __init__(self, name: str, version: str, system: str, backend: str, distro: str, path: str) -> None:
        # foundational
        self.name: str = name
        self.version: Version = Version(str(version))
        self.system: str = system
        self.backend: str = backend
        self.distro: str = distro
        self.dependencies: list[str] = list()

        # additional
        self.variables: dict[str, str] = dict()
        self.arguments: list[str] = list()
        self.template: str = "default"
        self.files: list[str] = list()
        self.prolog: str | None = None

        # metadata
        self.path: Path = Path(path)

    def satisfies(self, spec: str) -> bool:
        """Test if this node satisfies the given spec."""
        name_version_regex: str = \
            r"^(?P<name>{})(?:(?:@(?P<left>[\d\.]+)(?!@))?(?:@?(?P<colen>:)(?P<right>[\d\.]+)?)?)?$".format(self.name)
        system_regex: str = r"^system=(?P<system>[a-zA-Z0-9]+)$"
        backend_regex: str = r"^backend=(?P<backend>[a-zA-Z0-9]+)$"
        distro_regex: str = r"^distro=(?P<distro>[a-zA-Z0-9]+)$"
        dependency_regex: str = r"^\^(?P<name>[a-zA-Z0-9-]+)$"

        ss: list[str] = re_split(r"\s+", spec.strip())

        for part in ss:
            # name and version
            res: ReMatch | None = re_fullmatch(name_version_regex, part)
            if res is not None:
                gd: dict = res.groupdict()
                if gd["left"] is not None and gd["right"] is None:  # n@v: or n@v
                    if gd["colen"] is not None:
                        if Version(gd["left"]) > self.version:
                            return False
                    else:
                        if Version(gd["left"]) != self.version:
                            return False
                elif gd["left"] is None and gd["right"] is not None:  # n@:v
                    if gd["colen"] is not None:
                        if Version(gd["right"]) < self.version:
                            return False
                    else:
                        return False
                elif gd["left"] is None and gd["right"] is None:  # n
                    if gd["colen"] is not None:
                        return False
                else:  # n@v:v
                    if Version(gd["left"]) > self.version or self.version > Version(gd["right"]):
                        return False
                continue  # part has been handled so continue

            # system
            res = re_fullmatch(system_regex, part)
            if res is not None:
                if res.group("system") != self.system:
                    return False
                continue  # part has been handled so continue

            # backend
            res = re_fullmatch(backend_regex, part)
            if res is not None:
                if res.group("backend") != self.backend:
                    return False
                continue  # part has been handled so continue

            # distro
            res = re_fullmatch(distro_regex, part)
            if res is not None:
                if res.group("distro") != self.distro:
                    return False
                continue  # part has been handled so continue

            # dependencies
            res = re_fullmatch(dependency_regex, part)
            if res is not None:
                matched = False
                for dep in self.dependencies:
                    if res.group("name") == dep:
                        matched = True
                if matched:
                    continue    # match is found so continue

            # if we get here this part has not been handled
            return False

        # all parts were handled
        return True

    def apply_constraint(self, conditional: str, _type: str, spec: str) -> bool:
        if self.satisfies(conditional):
            if _type == "dependency":
                self.dependencies.append(spec)
            elif _type == "variable":
                parts = spec.split("=")
                self.variables[parts[0]] = parts[1]
            elif _type == "argument":
                self.arguments.append(spec)
            elif _type == "template":
                self.template = spec
            elif self.files == "file":
                self.files.append(spec)
            elif _type == "prolog":
                self.prolog = spec
            else:
                # not a valid type
                return False
        else:
            # spec not added
            return False

    @property
    def hash(self) -> str:
        """Return a hash for this node uniquely identifying it."""

        hash_list: list = list()
        hash_list.append(self.name)
        hash_list.append(self.version)
        hash_list.append(self.system)
        hash_list.append(self.backend)
        hash_list.append(self.distro)
        hash_list.append(",".join(str(x) for x in self.dependencies))
        hash_list.append(",".join(str(x) for x in self.variables))
        hash_list.append(",".join(str(x) for x in self.arguments))
        tf = Path(self.path).joinpath("templates", self.template)
        if tf.is_file():
            hash_list.append(sha256(tf.read_bytes()).hexdigest())
        else:
            hash_list.append(None)
        hash_list.append(",".join(str(x) for x in self.files))
        hash_list.append(self.prolog)

        hash_str: str = "|".join(str(x) for x in hash_list)
        return sha256(hash_str.encode()).hexdigest()

    @property
    def id(self) -> str:
        return self.hash[:7]

    def __hash__(self) -> int:
        return int(self.hash, 16)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Image):
            return False
        return self.hash == other.hash

    def __lt__(self, other) -> bool:
        if isinstance(other, Image):
            return not self.version.preferred(other.version)
        return False

    def __str__(self) -> str:
        return "{} {}@{} system={} backend={} distro={}{}".format(
            self.hash[:7],
            self.name,
            self.version,
            self.system,
            self.backend,
            self.distro,
            "".join(" ^{}".format(x) for x in self.dependencies) if len(self.dependencies) > 0 else ""
        )


class DepOp(Enum):
    """
    Specify dependency options
    """
    EQ = '='
    GE = '>='
    LE = '<='
    UN = None


class Target:
    """
    Build specification targets
    """

    def __init__(self, node: Image, op: DepOp):
        self.node = node
        self.op = op

    def __str__(self):
        return f'Target: {self.op} -> {str(self.node)}'


class ImageGraph(nx_DiGraph):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def add_edge(self, u_of_edge: Image, v_of_edge: Image, **attr) -> None:
        # check that edge endpoint are in graph
        if self.has_node(u_of_edge) and self.has_node(v_of_edge):
            super().add_edge(u_of_edge, v_of_edge, **attr)
        else:
            raise InvalidDependencySpecification(f'{v_of_edge.name}@{v_of_edge.version}',
                                                 u_of_edge.name, u_of_edge.version,
                                                 Path.joinpath(u_of_edge.path, 'specs.yaml'))

        # check that graph is still a DAG
        if not nx_is_directed_acyclic_graph(self):
            cycle = nx_find_cycle(self)
            raise EdgeViolatesDAG(u_of_edge, v_of_edge, cycle)

    def get_similar_nodes(self, node: Image) -> set:
        similar = set()
        for n in self.nodes:
            if n.satisfies(node.name):
                similar.add(n)
        return similar

    def get_dependencies(self, node: Image) -> set[Image]:
        # had to add this wrapper because nx.neighbors was dropping the attributes of some nodes (cuda, python)
        deps = set()
        for node in nx_neighbors(self, node):
            for n in self.nodes:
                if n == node:
                    deps.add(n)
        # will contact the maintainers of networkx at some point

        return deps

    def is_above(self, u_node: Image, v_node: Image) -> bool:
        """
        Test if one node is above another in the dependency tree
        """
        return nx_has_path(self, u_node, v_node)

    def _is_valid_build_tuple(self, bt: tuple[Image]) -> bool:
        """
        Verify that all the dependencies of a build tuple can be met.
        """
        valid = True

        # check for similar images
        for i0 in range(len(bt)):
            for i2 in bt[i0 + 1:]:
                if bt[i0].satisfies(i2.name):
                    valid = False

        # check that all images exist
        for node in bt:
            if not self.has_node(node):
                valid = False

        # break prematurely if the first two checks fail
        if not valid:
            return valid

        # check that deps in build tuple
        for node in bt:
            deps = self.get_dependencies(node)

            # group deps
            grouped = dict()
            for d in deps:
                if d.name not in grouped:
                    grouped[d.name] = set()
                grouped[d.name].add(d)

            # check that the needed dependency exists
            for g in grouped:
                if grouped[g].isdisjoint(bt):
                    valid = False

        return valid

    def create_build_recipe(self, targets: list[Target]) -> tuple:

        # check if all the targets exist
        for node in targets:
            if len(self.get_similar_nodes(node.node)) < 1:
                raise NoAvailableBuild(f"The build target {node.node} does not exist!")

        # init build set and priority list
        build_set = set()
        priority_list = list()

        # add similar to build set
        for target in targets:
            build_set.update(self.get_similar_nodes(target.node))
            # make sure to update priority
            if target.node.name not in priority_list:
                priority_list.append(target.node.name)

        # add deps to build set
        while True:
            build_set_length = len(build_set)

            for node in build_set.copy():
                dependencies = self.get_dependencies(node)
                for d in dependencies:
                    build_set.add(d)
                    if d.name not in priority_list:
                        priority_list.append(d.name)

            # loop until all dependencies are added
            if build_set_length == len(build_set):
                break

        # apply constraints
        for target in targets:
            for node in build_set.copy():
                if node.satisfies(target.node.name):
                    if target.op == DepOp.EQ and node.version != target.node.version:
                        build_set.remove(node)
                    elif target.op == DepOp.GE and node.version < target.node.version:
                        build_set.remove(node)
                    elif target.op == DepOp.LE and node.version > target.node.version:
                        build_set.remove(node)

        # group deps
        grouped = dict()
        for node in build_set:
            if node.name not in grouped:
                grouped[node.name] = set()
            grouped[node.name].add(node)
        # sort deps so that the highest versions of images further up the dep tree will be chosen
        prioritized_list_group = list()
        for group in priority_list:
            tmp = list(grouped[group])
            tmp.sort(reverse=True)
            prioritized_list_group.append(tmp)
        # get permutations
        permutations = get_permutations(0, prioritized_list_group)

        # return valid build tuple
        for p in permutations:

            # clean up permutation
            clean_p = set()
            for n in p:
                for t in targets:
                    con_targ = None
                    for nt in [x for x in p]:
                        if nt.satisfies(t.node.name):
                            con_targ = nt
                            break
                    if self.is_above(con_targ, n):
                        clean_p.add(n)
                        break

            if self._is_valid_build_tuple(tuple(clean_p)):
                # order build
                build_list = list()
                processed = set()
                unprocessed = clean_p.copy()
                while len(unprocessed) > 0:
                    level_holder = list()
                    for node in unprocessed.copy():
                        deps = set(self.get_dependencies(node)).intersection(clean_p)
                        if deps.issubset(processed):
                            level_holder.append(node)
                    level_holder.sort()
                    for node in level_holder:
                        processed.add(node)
                        unprocessed.remove(node)
                        build_list.append(node)

                return tuple(build_list)

        # if we got here no valid build tuple could be found
        raise NoAvailableBuild("No Available build!")


class ImageRepo:
    def __init__(self) -> None:
        # constraint(image, condition, type, spec, scope)
        self.constraints: list[tuple[str, str, str, str, str]] = list()
        self.images: set[Image] = set()

    def import_from_dir(self, path: str) -> None:
        """Add Images from path."""
        p = Path(path)
        if not p.is_dir():
            raise NotADirectoryError(f"Image path {path} is not a directory!")

        for name in [x for x in p.iterdir() if x.is_dir() and x.name[0] != '.']:
            with open(name.joinpath("specs.yaml"), "r") as fi:
                specs = yaml_safe_load(fi)
                # add versions
                for version in specs["versions"]:
                    image = Image(
                        name.name,
                        version["spec"],
                        config.get("velocity:system"),
                        config.get("velocity:backend"),
                        config.get("velocity:distro"),
                        str(name)
                    )
                    if "when" in version:
                        if image.satisfies(version["when"]):
                            self.images.add(image)
                    else:
                        self.images.add(image)

                # add constraints
                # dependencies
                if "dependencies" in specs:
                    for dependency in specs["dependencies"]:
                        self.constraints.append((
                            name.name,
                            dependency["when"] if "when" in dependency else "",
                            "dependency",
                            dependency["spec"],
                            dependency["scope"] if "scope" in dependency else "image"
                        ))
                # templates
                if "templates" in specs:
                    for template in specs["templates"]:
                        self.constraints.append((
                            name.name,
                            template["when"] if "when" in template else "",
                            "template",
                            template["path"],
                            template["scope"] if "scope" in template else "image"
                        ))
                # arguments
                if "arguments" in specs:
                    for argument in specs["arguments"]:
                        self.constraints.append((
                            name.name,
                            argument["when"] if "when" in argument else "",
                            "argument",
                            argument["value"],
                            argument["scope"] if "scope" in argument else "image"
                        ))
                # variables
                if "variables" in specs:
                    for variable in specs["variables"]:
                        self.constraints.append((
                            name.name,
                            variable["when"] if "when" in variable else "",
                            "variable",
                            "{}={}".format(variable["name"], variable["value"]),
                            variable["scope"] if "scope" in variable else "image"
                        ))
                # files
                if "files" in specs:
                    for file in specs["files"]:
                        self.constraints.append((
                            name.name,
                            file["when"] if "when" in file else "",
                            "file",
                            file["name"],
                            file["scope"] if "scope" in file else "image"
                        ))
                # prologs
                if "prologs" in specs:
                    for prolog in specs["prologs"]:
                        self.constraints.append((
                            name.name,
                            prolog["when"] if "when" in prolog else "",
                            "prolog",
                            prolog["script"],
                            prolog["scope"] if "scope" in prolog else "image"
                        ))

    def create_build_recipe(self, targets: list[str]) -> tuple:
        images = deepcopy(self.images)

        build_targets = list()
        targs = list()
        for t in targets:
            res = re_fullmatch(
                r"^(?P<name>[a-zA-Z0-9-]+)(?:(?:@(?P<left>[\d\.]+)(?!@))?(?:@?(?P<colen>:)(?P<right>[\d\.]+)?)?)?$",
                t
            )
            if res is not None:
                gd: dict = res.groupdict()
                if gd["left"] is not None and gd["right"] is None:  # n@v: or n@v
                    if gd["colen"] is not None:
                        t = Image(
                                gd["name"],
                                gd["left"],
                                config.get("velocity:system"),
                                config.get("velocity:backend"),
                                config.get("velocity:distro"),
                                ""
                            )
                        build_targets.append(Target(
                            t,
                            DepOp.GE
                        ))
                        targs.append(t)
                    else:
                        t = Image(
                                gd["name"],
                                gd["left"],
                                config.get("velocity:system"),
                                config.get("velocity:backend"),
                                config.get("velocity:distro"),
                                ""
                            )
                        build_targets.append(Target(
                            t,
                            DepOp.EQ
                        ))
                        targs.append(t)
                elif gd["left"] is None and gd["right"] is not None:  # n@:v
                    if gd["colen"] is not None:
                        t = Image(
                                gd["name"],
                                gd["right"],
                                config.get("velocity:system"),
                                config.get("velocity:backend"),
                                config.get("velocity:distro"),
                                ""
                            )
                        build_targets.append(Target(
                            t,
                            DepOp.LE
                        ))
                        targs.append(t)
                    else:
                        raise InvalidImageVersionError()
                elif gd["left"] is None and gd["right"] is None:  # n
                    if gd["colen"] is not None:
                        raise InvalidImageVersionError()
                    else:
                        t = Image(
                                gd["name"],
                                "",
                                config.get("velocity:system"),
                                config.get("velocity:backend"),
                                config.get("velocity:distro"),
                                ""
                            )
                        build_targets.append(Target(
                            t,
                            DepOp.EQ
                        ))
                        targs.append(t)
                else:  # n@v:v
                    t = Image(
                            gd["name"],
                            gd["left"],
                            config.get("velocity:system"),
                            config.get("velocity:backend"),
                            config.get("velocity:distro"),
                            ""
                        )
                    build_targets.append(Target(
                        t,
                        DepOp.GE
                    ))
                    targs.append(t)
                    t = Image(
                            gd["name"],
                            gd["right"],
                            config.get("velocity:system"),
                            config.get("velocity:backend"),
                            config.get("velocity:distro"),
                            ""
                        )
                    build_targets.append(Target(
                        t,
                        DepOp.LE
                    ))
                    targs.append(t)
            else:
                raise NoAvailableBuild("No available build!")

        # apply constraints
        for constraint in self.constraints:
            if constraint[4] == "build":
                for targ in targs:
                    if targ.satisfies(constraint[1]):
                        for image in images:
                            image.apply_constraint(
                                constraint[0],
                                constraint[2],
                                constraint[3]
                            )

            else:   # default is image
                for image in images:
                    image.apply_constraint(
                        "{} {}".format(constraint[0], constraint[1]),
                        constraint[2],
                        constraint[3]
                    )

        ig = ImageGraph()
        for image in images:
            ig.add_node(image)
        for image in images:
            for dep in image.dependencies:
                for di in images:
                    if di.satisfies(dep):
                        ig.add_edge(image, di)

        return ig.create_build_recipe(build_targets)

