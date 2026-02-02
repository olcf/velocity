"""Graph library and tools for dependency graph"""

from copy import deepcopy
from enum import Enum
from hashlib import sha256
from pathlib import Path
from re import (
    Match as ReMatch,
    Pattern as RePattern,
    compile as re_compile,
    fullmatch as re_fullmatch,
    split as re_split,
)
from timeit import default_timer as timer

from colorama import Fore, Style
from loguru import logger
from networkx import (
    DiGraph as nx_DiGraph,
    find_cycle as nx_find_cycle,
    is_directed_acyclic_graph as nx_is_directed_acyclic_graph,
    neighbors as nx_neighbors,
)
from typing_extensions import Self
from yaml import safe_load as yaml_safe_load

from ._config import config
from ._exceptions import (
    CannotFindDependency,
    EdgeViolatesDAG,
    InvalidImageVersionError,
    NoAvailableBuild,
    SpecSyntaxError,
)
from ._print import TextBlock, header_print, indent_print
from ._tools import OurMeta, trace_function

# variables
EMPTY_STR: str = ""

TARGET_REGEX: RePattern = re_compile(
    r"^(?P<name>[a-zA-Z0-9-]+)(?:(?:@(?P<left>[^:\s]+)(?!@))?(?:@?(?P<colon>:)(?P<right>\S+)?)?)?$"
)
SYSTEM_REGEX: RePattern = re_compile(r"^system=(?P<system>[a-zA-Z0-9]+)$")
BACKEND_REGEX: RePattern = re_compile(r"^backend=(?P<backend>[a-zA-Z0-9]+)$")
DISTRO_REGEX: RePattern = re_compile(r"^distro=(?P<distro>[a-zA-Z0-9]+)$")
DEPENDENCY_REGEX: RePattern = re_compile(r"^\^(?P<name>[a-zA-Z0-9-]+)$")

VARIABLE_REGEX: RePattern = re_compile(r"^(?P<key>[^=]+)=(?P<value>.*)$")

VERSION_REGEX: RePattern = re_compile(
    r"^(?P<major>[0-9]+)(?:\.(?P<minor>[0-9]+)(:?\.(?P<patch>[0-9]+))?)?(?:-(?P<suffix>[a-zA-Z0-9]+))?$"
)


@trace_function
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
        sub_permutations = get_permutations(idx + 1, sets)
        for i in sets[idx]:
            for sub in sub_permutations:
                permutations.append(sub.union({i}))
    return permutations


class Version(metaclass=OurMeta):
    """Version class."""

    def __init__(self, version_specifier: str) -> None:
        self.vs = version_specifier
        try:
            version_dict: dict = VERSION_REGEX.fullmatch(version_specifier).groupdict()
            self.major: int | None = int(version_dict["major"]) if version_dict["major"] else None
            self.minor: int | None = int(version_dict["minor"]) if version_dict["minor"] else None
            self.patch: int | None = int(version_dict["patch"]) if version_dict["patch"] else None
            self.suffix: str | None = str(version_dict["suffix"]) if version_dict["suffix"] else None
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
            self.major if self.major else "#",
            self.minor if self.minor else "#",
            self.patch if self.patch else "#",
            self.suffix if self.suffix else "~",
        )

    def preferred(self, other) -> bool:
        """Determine which version to prefer when two version are "equal" ex. 12.3 vs 12.3.0-rc1"""
        return self.vcs > other.vcs

    @property
    def _vcs_t(self) -> str:
        """Version Comparison String Truncated"""
        vl: int = 0
        if not self.major:
            pass
        elif not self.minor:
            vl = 9
        elif not self.patch:
            vl = 19
        elif not self.suffix:
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
            raise TypeError(
                f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'"
            )
        s_vcs, o_vcs = self._cut_vcses_to_size(self, other)
        return s_vcs == o_vcs

    def __ne__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'"
            )
        s_vcs, o_vcs = self._cut_vcses_to_size(self, other)
        return s_vcs != o_vcs

    def __gt__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'"
            )
        return self.vcs > other.vcs and not self.__eq__(other)

    def __ge__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'"
            )
        return self.vcs > other.vcs or self.__eq__(other)

    def __lt__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'"
            )
        return self.vcs < other.vcs and not self.__eq__(other)

    def __le__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of '{type(self).__name__}' and '{type(other).__name__}'"
            )
        return self.vcs < other.vcs or self.__eq__(other)

    def __str__(self) -> str:
        return self.vs


class Image(metaclass=OurMeta):
    """Velocity container image."""

    def __init__(self, name: str, version: str, system: str, backend: str, distro: str, path: str) -> None:
        # foundational
        self.name: str = name
        self.version: Version = Version(str(version))
        self.system: str = system
        self.backend: str = backend
        self.distro: str = distro
        self.dependencies: set[str] = set()

        # additional
        self.variables: dict[str, str] = dict()
        self.arguments: set[str] = set()
        self.template: str = "default"
        self.files: set[str] = set()
        self.prolog: str | None = None
        self.underlay: int | None = None  # sum of the ids this image will be built on

        # metadata
        self.path: Path = Path(path)

        # extra
        self.name_version_regex: RePattern = re_compile(
            r"^(?P<name>{})(?:(?:@(?P<left>[\d\.]+)(?!@))?(?:@?(?P<colen>:)(?P<right>[\d\.]+)?)?)?$".format(self.name)
        )

    def satisfies(self, spec: str) -> bool:
        """Test if this node satisfies the given spec."""

        # return true if spec has no condition
        if spec.isspace():
            return True

        # else evaluate conditional
        ss: list[str] = re_split(r"\s+", spec.strip())

        for part in ss:
            # name and version
            res: ReMatch | None = self.name_version_regex.fullmatch(part)
            if res:
                gd: dict = res.groupdict()
                if gd["left"] and not gd["right"]:  # n@v: or n@v
                    if gd["colen"]:
                        if Version(gd["left"]) > self.version:
                            return False
                    else:
                        if Version(gd["left"]) != self.version:
                            return False
                elif not gd["left"] and gd["right"]:  # n@:v
                    if gd["colen"]:
                        if Version(gd["right"]) < self.version:
                            return False
                    else:
                        return False
                elif not gd["left"] and not gd["right"]:  # n
                    if gd["colen"]:
                        return False
                else:  # n@v:v
                    if Version(gd["left"]) > self.version or self.version > Version(gd["right"]):
                        return False
                continue  # part has been handled so continue

            # system
            res = SYSTEM_REGEX.fullmatch(part)
            if res:
                if res.group("system") != self.system:
                    return False
                continue  # part has been handled so continue

            # backend
            res = BACKEND_REGEX.fullmatch(part)
            if res:
                if res.group("backend") != self.backend:
                    return False
                continue  # part has been handled so continue

            # distro
            res = DISTRO_REGEX.fullmatch(part)
            if res:
                if res.group("distro") != self.distro:
                    return False
                continue  # part has been handled so continue

            # dependencies
            res = DEPENDENCY_REGEX.fullmatch(part)
            if res:
                matched = False
                for dep in self.dependencies:
                    if res.group("name") == dep:
                        matched = True
                if matched:
                    continue  # match is found so continue

            # if we get here this part has not been handled
            return False

        # all parts were handled
        return True

    def apply_constraint(self, conditional: str, _type: str, spec: str) -> bool:
        """Evaluate and apply constraints. Return True if a constraint changes the dependencies."""
        if self.satisfies(conditional):
            if _type == "dependency":
                if spec not in self.dependencies:
                    self.dependencies.add(spec)
                    return True
            elif _type == "variable":
                parts = VARIABLE_REGEX.fullmatch(spec).groupdict()
                self.variables[parts["key"]] = parts["value"]
            elif _type == "argument":
                self.arguments.add(spec)
            elif _type == "template":
                self.template = spec
            elif _type == "file":
                self.files.add(spec)
            elif _type == "prolog":
                self.prolog = spec
        return False

    @property
    def hash(self) -> str:
        """Return a hash for this node uniquely identifying it."""

        hash_list: list = list()
        hash_list.append(self.name)
        hash_list.append(self.version)
        hash_list.append(self.system)
        # hash_list.append(self.backend) # disable backend for now because it should not make a difference in the image
        hash_list.append(self.distro)
        hash_list.append(",".join(str(x) for x in sorted(self.dependencies)))
        hash_list.append(",".join(str(x) for x in sorted(self.variables)))
        hash_list.append(",".join(str(x) for x in sorted(self.arguments)))
        tf = Path(self.path).joinpath("templates", "{}.vtmp".format(self.template))
        if tf.is_file():
            hash_list.append(sha256(tf.read_bytes()).hexdigest())
        else:
            hash_list.append(None)
        hash_list.append(",".join(str(x) for x in sorted(self.files)))
        hash_list.append(self.prolog)
        hash_list.append(self.underlay)

        hash_str: str = "|".join(str(x) for x in hash_list)
        logger.debug(f"hash string for {self.name}: {hash_str}")
        return sha256(hash_str.encode()).hexdigest()

    @property
    def id(self) -> str:
        """Short hash."""
        return self.hash[:7]

    def __hash__(self) -> int:
        return int(self.hash, 16)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Image):
            return False
        return self.hash == other.hash

    def __lt__(self, other) -> bool:
        if isinstance(other, Image):
            # need to consider the name of the images as well
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
            "".join(" ^{}".format(x) for x in self.dependencies) if len(self.dependencies) > 0 else "",
        )


class DepOp(Enum):
    """Dependency options."""

    EQ = "="
    GE = ">="
    LE = "<="
    UN = None


class Target(metaclass=OurMeta):
    """Build targets."""

    def __init__(self, node: Image, op: DepOp):
        self.node: Image = node
        self.op: DepOp = op

    def __str__(self):
        return "Target: {} -> {}".format(self.op, self.node)


class ImageGraph(nx_DiGraph, metaclass=OurMeta):
    """Image dependency graph."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def add_edges_from(self, edges: list[tuple[Image, Image]], **kwargs) -> None:
        logger.info("Adding edges to graph")
        # check that edge endpoints are in graph
        nodes = set()
        for edge in edges:
            nodes.update(edge)
        for node in nodes:
            if not self.has_node(node):
                raise CannotFindDependency("Cannot find dependency '{}'.".format(node))

        super().add_edges_from(edges, **kwargs)

        # check that graph is still a DAG
        if not nx_is_directed_acyclic_graph(self):
            cycle = nx_find_cycle(self)
            raise EdgeViolatesDAG(cycle)

    def get_similar_nodes(self, node: Image) -> set:
        """Get all nodes with the same name."""
        similar = set()
        for n in self.nodes:
            if n.satisfies(node.name):
                similar.add(n)
        return similar

    def _is_valid_build_tuple(self, bt: tuple[Image]) -> bool:
        """Verify that all the dependencies in a build tuple are met."""
        # check that deps in build tuple
        for node in bt:
            deps = set(nx_neighbors(self, node))

            # group deps
            grouped = dict()
            for d in deps:
                if d.name not in grouped:
                    grouped[d.name] = set()
                grouped[d.name].add(d)

            # check that the needed dependency exists
            for g in grouped:
                if grouped[g].isdisjoint(bt):
                    return False

        return True

    def solve_build(self, targets: list[Target]) -> tuple:
        """Create a build recipe."""
        logger.info("solving for build recipe")
        # check if all the targets exist
        for node in targets:
            if len(self.get_similar_nodes(node.node)) < 1:
                raise NoAvailableBuild(f"The build target {node.node} does not exist!")

        # init build set and priority list
        build_set = set()
        build_names = set()

        # add similar to build set
        logger.info("loading similar images")
        for target in targets:
            build_set.update(self.get_similar_nodes(target.node))
            build_names.add(target.node.name)

        # add deps to build set
        logger.info("adding dependencies to build")
        while True:
            build_set_length = len(build_set)

            for node in build_set.copy():
                dependencies = set(nx_neighbors(self, node))
                # logger.info(dependencies)
                build_set.update(dependencies)
                build_names.update([_.name for _ in dependencies])

            # loop until all dependencies are added
            if build_set_length == len(build_set):
                break

        # apply constraints
        logger.info("apply target constraints")
        for target in targets:
            for node in build_set.copy():
                if node.satisfies(target.node.name):
                    if target.op == DepOp.EQ and node.version != target.node.version:
                        build_set.remove(node)
                    elif target.op == DepOp.GE and node.version < target.node.version:
                        build_set.remove(node)
                    elif target.op == DepOp.LE and node.version > target.node.version:
                        build_set.remove(node)

        logger.info("group and prioritize build")
        # group deps
        grouped: dict = dict()
        for node in build_set:
            if node.name not in grouped:
                grouped[node.name] = set()
            grouped[node.name].add(node)
        # sort deps so that the highest versions of images further up the dep tree will be chosen
        prioritized_list_group: list[list] = list()
        for group in build_names:
            tmp = list(grouped[group])
            tmp.sort(reverse=True)
            prioritized_list_group.append(tmp)

        # get permutations
        logger.info("get build permutations")
        permutations = get_permutations(0, prioritized_list_group)

        # return valid build tuple
        logger.info("examining build permutations")
        for p in permutations:
            if self._is_valid_build_tuple(tuple(p)):
                # order build
                build_list = list()
                processed = set()
                unprocessed = p.copy()
                while len(unprocessed) > 0:
                    level_holder = list()
                    for node in unprocessed.copy():
                        deps = set(nx_neighbors(self, node)).intersection(p)
                        if deps.issubset(processed):
                            level_holder.append(node)
                    level_holder.sort()
                    processed.update(level_holder)
                    build_list.extend(level_holder)
                    for node in level_holder:
                        unprocessed.remove(node)

                return tuple(build_list)

        # if we got here no valid build tuple could be found
        raise NoAvailableBuild("No Available build!")


class ImageRepo(metaclass=OurMeta):
    """Image repository."""

    def __init__(self) -> None:
        logger.info("creating image repo")
        self.images: set[Image] = set()

        # constraint(image, condition, type, spec, scope(only for versions and dependencies))
        logger.info("loading global image constraints")
        self.constraints: list[tuple[str, str, str, str, str]] = list()
        if cstrs := config.get("constraints", warn_on_miss=False):
            logger.debug(f"global constraints: {cstrs}")
            # arguments
            if "arguments" in cstrs:
                for argument in cstrs["arguments"]:
                    if isinstance(argument["value"], list):
                        specs = argument["value"]
                    else:
                        specs = [
                            argument["value"],
                        ]
                    for spec in specs:
                        self.constraints.append(
                            (EMPTY_STR, argument["when"] if "when" in argument else EMPTY_STR, "argument", spec)
                        )
            # variables
            if "variables" in cstrs:
                for variable in cstrs["variables"]:
                    self.constraints.append(
                        (
                            EMPTY_STR,
                            variable["when"] if "when" in variable else EMPTY_STR,
                            "variable",
                            "{}={}".format(variable["name"], variable["value"]),
                        )
                    )

    def import_from_dir(self, path: str) -> None:
        """Add Images from path."""
        p = Path(path)
        if not p.is_dir():
            raise NotADirectoryError(f"Image path {path} is not a directory!")
        logger.info(f"importing images from {p}")

        imported_names = set()
        for image_path in [_ for _ in p.iterdir() if _.is_dir() and _.name[0] != "."]:
            name = image_path.name
            # check for duplicate image
            if name in imported_names:
                logger.warn(
                    "The image definition in '{}' is being skipped because it has the same name as an already imported image.".format(
                        name
                    )
                )
                continue
            imported_names.add(name)

            # process metadata
            logger.info(f"importing image {name}")
            with open(image_path.joinpath("specs.yaml"), "r") as f:
                try:
                    specs_file = yaml_safe_load(f)
                    # add versions
                    for version in specs_file["versions"]:
                        if isinstance(version["spec"], list):
                            specs = version["spec"]
                        else:
                            specs = [
                                version["spec"],
                            ]
                        for spec in specs:
                            image = Image(
                                name,
                                spec,
                                config.get("velocity:system"),
                                config.get("velocity:backend"),
                                config.get("velocity:distro"),
                                str(image_path),
                            )
                            if "when" in version:
                                if not image.satisfies(version["when"]):
                                    continue
                            self.images.add(image)
                    # add constraints
                    # dependencies
                    if "dependencies" in specs_file:
                        for dependency in specs_file["dependencies"]:
                            if isinstance(dependency["spec"], list):
                                specs = dependency["spec"]
                            else:
                                specs = [
                                    dependency["spec"],
                                ]
                            for spec in specs:
                                if "^" in spec:
                                    raise SpecSyntaxError("'^' not allowed in dependency spec.")
                                self.constraints.append(
                                    (
                                        name,
                                        dependency["when"] if "when" in dependency else EMPTY_STR,
                                        "dependency",
                                        spec,
                                        dependency["scope"] if "scope" in dependency else "image",
                                    )
                                )
                    # templates
                    if "templates" in specs_file:
                        for template in specs_file["templates"]:
                            self.constraints.append(
                                (
                                    name,
                                    template["when"] if "when" in template else EMPTY_STR,
                                    "template",
                                    template["name"],
                                )
                            )
                    # arguments
                    if "arguments" in specs_file:
                        for argument in specs_file["arguments"]:
                            if isinstance(argument["value"], list):
                                specs = argument["value"]
                            else:
                                specs = [
                                    argument["value"],
                                ]
                            for spec in specs:
                                self.constraints.append(
                                    (
                                        name,
                                        argument["when"] if "when" in argument else EMPTY_STR,
                                        "argument",
                                        spec,
                                    )
                                )
                    # variables
                    if "variables" in specs_file:
                        for variable in specs_file["variables"]:
                            self.constraints.append(
                                (
                                    name,
                                    variable["when"] if "when" in variable else EMPTY_STR,
                                    "variable",
                                    "{}={}".format(variable["name"], variable["value"]),
                                )
                            )
                    # files
                    if "files" in specs_file:
                        for file in specs_file["files"]:
                            if isinstance(file["name"], list):
                                specs = file["name"]
                            else:
                                specs = [
                                    file["name"],
                                ]
                            for spec in specs:
                                self.constraints.append(
                                    (
                                        name,
                                        file["when"] if "when" in file else "",
                                        "file",
                                        spec,
                                    )
                                )
                    # prologs
                    if "prologs" in specs_file:
                        for prolog in specs_file["prologs"]:
                            self.constraints.append(
                                (
                                    name,
                                    prolog["when"] if "when" in prolog else "",
                                    "prolog",
                                    prolog["script"],
                                )
                            )
                except TypeError as e:
                    logger.error(e)
                    logger.critical("Error in configuration file '{}'!".format(name.joinpath("specs.yaml")))
                    exit(1)

    def create_build_recipe(self, targets: list[str]) -> tuple[tuple, ImageGraph]:
        """Create an ordered build recipe of images."""
        header_print([TextBlock("Creating build recipe:")])
        start = timer()

        logger.info("start image recipe creation")
        images: set[Image] = deepcopy(self.images)

        logger.info("parsing targets")
        build_targets: list[Target] = list()
        for target in targets:
            if res := TARGET_REGEX.fullmatch(target):
                gd: dict = res.groupdict()
                system = config.get("velocity:system")
                backend = config.get("velocity:backend")
                distro = config.get("velocity:distro")

                # n@v: or n@v
                if gd["left"] and not gd["right"]:
                    t = Image(
                        gd["name"],
                        gd["left"],
                        system,
                        backend,
                        distro,
                        EMPTY_STR,
                    )
                    if gd["colon"]:
                        build_targets.append(Target(t, DepOp.GE))
                    else:
                        build_targets.append(Target(t, DepOp.EQ))
                # n@:v
                elif not gd["left"] and gd["right"]:
                    if not gd["colon"]:
                        raise InvalidImageVersionError("Invalid version '{}'.".format(target))
                    t = Image(
                        gd["name"],
                        gd["right"],
                        system,
                        backend,
                        distro,
                        EMPTY_STR,
                    )
                    build_targets.append(Target(t, DepOp.LE))
                # n
                elif not gd["left"] and not gd["right"]:
                    if gd["colon"]:
                        raise InvalidImageVersionError("Invalid version '{}'.".format(target))
                    t = Image(
                        gd["name"],
                        "",
                        config.get("velocity:system"),
                        config.get("velocity:backend"),
                        config.get("velocity:distro"),
                        EMPTY_STR,
                    )
                    build_targets.append(Target(t, DepOp.UN))
                # n@v:v
                else:
                    t = Image(
                        gd["name"],
                        gd["left"],
                        config.get("velocity:system"),
                        config.get("velocity:backend"),
                        config.get("velocity:distro"),
                        EMPTY_STR,
                    )
                    build_targets.append(Target(t, DepOp.GE))
                    t = Image(
                        gd["name"],
                        gd["right"],
                        config.get("velocity:system"),
                        config.get("velocity:backend"),
                        config.get("velocity:distro"),
                        EMPTY_STR,
                    )
                    build_targets.append(Target(t, DepOp.LE))
            else:
                raise NoAvailableBuild("No available build!")

        # pre-burner graph
        logger.info("setting up pre-burner graph")
        for constraint in self.constraints:
            for image in images:
                image.apply_constraint("{} {}".format(constraint[0], constraint[1]), constraint[2], constraint[3])
        ig = ImageGraph()
        ig.add_nodes_from(images)
        edges: list[tuple] = list()
        for image in images:
            for dep in image.dependencies:
                for di in images:
                    if di.satisfies(dep):
                        edges.append((image, di))
        ig.add_edges_from(edges)

        logger.info("creating pre-burner recipe")
        bt: tuple[Image] = ig.solve_build(build_targets)

        # apply constraints for the build scope
        logger.info("applying constraints for the build")
        images_changed: bool = True
        while images_changed:
            images_changed = False
            for constraint in self.constraints:
                if constraint[2] == "dependency" and constraint[4] == "build":
                    for b_target in bt:
                        if b_target.satisfies(constraint[1]):
                            for image in images:
                                if image.apply_constraint(constraint[0], constraint[2], constraint[3]):
                                    images_changed = True
        for constraint in self.constraints:
            for image in images:
                image.apply_constraint("{} {}".format(constraint[0], constraint[1]), constraint[2], constraint[3])

        # create graph
        logger.info("creating final image graph")
        ig = ImageGraph()
        ig.add_nodes_from(images)
        edges = list()
        for image in images:
            for dep in image.dependencies:
                for di in images:
                    if di.satisfies(dep):
                        edges.append((image, di))
        ig.add_edges_from(edges)

        logger.info("creating final recipe")
        bt: tuple[Image] = ig.solve_build(build_targets)

        # update images so that their hash includes the layers below them
        logger.info("updating image hashes with dependencies")
        cumulative_deps: int = 0
        for b in bt:
            b.underlay = cumulative_deps
            cumulative_deps = cumulative_deps + int(b.id, 16)

        logger.info("creating recipe image graph")
        bt_ig = ImageGraph()
        bt_ig.add_nodes_from(bt)
        edges = list()
        for image in bt:
            for dep in image.dependencies:
                for di in bt:
                    if di.satisfies(dep):
                        edges.append((image, di))
        bt_ig.add_edges_from(edges)

        logger.info("build recipe created")

        end = timer()
        indent_print(
            [TextBlock(f"created recipe in {round(end - start, 2)}s\n", fore=Fore.MAGENTA, style=Style.BRIGHT)]
        )

        return bt, bt_ig
