"""Graph library and tools for dependency graph"""

from loguru import logger
from re import split as re_split, fullmatch as re_fullmatch, Match as ReMatch
from pathlib import Path
from hashlib import sha256
from typing_extensions import Self
from yaml import safe_load as yaml_safe_load
from copy import deepcopy
from enum import Enum
from networkx import (
    DiGraph as nx_DiGraph,
    is_directed_acyclic_graph as nx_is_directed_acyclic_graph,
    find_cycle as nx_find_cycle,
    neighbors as nx_neighbors,
    has_path as nx_has_path,
)
from ._config import config
from ._exceptions import InvalidImageVersionError, CannotFindDependency, EdgeViolatesDAG, NoAvailableBuild
from ._tools import OurMeta, trace_function


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
        for i in sets[idx]:
            sub_permutations = get_permutations(idx + 1, sets)
            for sub in sub_permutations:
                permutations.append(sub.union({i}))
    return permutations


class Version(metaclass=OurMeta):
    """Version class."""

    def __init__(self, version_specifier: str) -> None:
        self.vs = version_specifier
        try:
            version_dict: dict = re_fullmatch(
                r"^(?P<major>[0-9]+)(?:\.(?P<minor>[0-9]+)(:?\.(?P<patch>[0-9]+))?)?(?:-(?P<suffix>[a-zA-Z0-9]+))?$",
                version_specifier,
            ).groupdict()
            self.major: int | None = int(version_dict["major"]) if version_dict["major"] is not None else None
            self.minor: int | None = int(version_dict["minor"]) if version_dict["minor"] is not None else None
            self.patch: int | None = int(version_dict["patch"]) if version_dict["patch"] is not None else None
            self.suffix: str | None = str(version_dict["suffix"]) if version_dict["suffix"] is not None else None
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
            self.suffix if self.suffix is not None else "~",
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
            raise TypeError(
                f"'>' not supported between instances of " f"'{type(self).__name__}' and '{type(other).__name__}'"
            )
        s_vcs, o_vcs = self._cut_vcses_to_size(self, other)
        return s_vcs == o_vcs

    def __ne__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of " f"'{type(self).__name__}' and '{type(other).__name__}'"
            )
        s_vcs, o_vcs = self._cut_vcses_to_size(self, other)
        return s_vcs != o_vcs

    def __gt__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of " f"'{type(self).__name__}' and '{type(other).__name__}'"
            )
        return self.vcs > other.vcs and not self.__eq__(other)

    def __ge__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of " f"'{type(self).__name__}' and '{type(other).__name__}'"
            )
        return self.vcs > other.vcs or self.__eq__(other)

    def __lt__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of " f"'{type(self).__name__}' and '{type(other).__name__}'"
            )
        return self.vcs < other.vcs and not self.__eq__(other)

    def __le__(self, other) -> bool:
        if not isinstance(other, Version):
            raise TypeError(
                f"'>' not supported between instances of " f"'{type(self).__name__}' and '{type(other).__name__}'"
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

    def satisfies(self, spec: str) -> bool:
        """Test if this node satisfies the given spec."""

        # return true if spec has no condition
        if re_fullmatch(r"^\s*$", spec):
            return True

        # else evaluate conditional
        name_version_regex: str = (
            r"^(?P<name>{})(?:(?:@(?P<left>[\d\.]+)(?!@))?(?:@?(?P<colen>:)(?P<right>[\d\.]+)?)?)?$".format(self.name)
        )
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
                parts = spec.split("=")
                self.variables[parts[0]] = parts[1]
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
        hash_list.append(",".join(str(x) for x in self.dependencies))
        hash_list.append(",".join(str(x) for x in self.variables))
        hash_list.append(",".join(str(x) for x in self.arguments))
        tf = Path(self.path).joinpath("templates", "{}.vtmp".format(self.template))
        if tf.is_file():
            hash_list.append(sha256(tf.read_bytes()).hexdigest())
        else:
            hash_list.append(None)
        hash_list.append(",".join(str(x) for x in self.files))
        hash_list.append(self.prolog)
        hash_list.append(self.underlay)

        hash_str: str = "|".join(str(x) for x in hash_list)
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
        self.node = node
        self.op = op

    def __str__(self):
        return "Target: {} -> {}".format(self.op, self.node)


class ImageGraph(nx_DiGraph, metaclass=OurMeta):
    """Image dependency graph."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def add_edge(self, u_of_edge: Image, v_of_edge: Image, **kwargs) -> None:
        # check that edge endpoints are in graph
        if self.has_node(u_of_edge) and self.has_node(v_of_edge):
            super().add_edge(u_of_edge, v_of_edge, **kwargs)
        else:
            raise CannotFindDependency("Cannot find dependency {} for {}".format(v_of_edge, u_of_edge))

        # check that graph is still a DAG
        if not nx_is_directed_acyclic_graph(self):
            cycle = nx_find_cycle(self)
            raise EdgeViolatesDAG(u_of_edge, v_of_edge, cycle)

    def get_similar_nodes(self, node: Image) -> set:
        """Get all nodes with the same name."""
        similar = set()
        for n in self.nodes:
            if n.satisfies(node.name):
                similar.add(n)
        return similar

    def get_dependencies(self, node: Image) -> set[Image]:
        """Get all dependencies for an image."""
        # had to add this wrapper because nx.neighbors was dropping the attributes of some nodes (cuda, python)
        deps = set()
        for node in nx_neighbors(self, node):
            for n in self.nodes:
                if n == node:
                    deps.add(n)
        # TODO will contact the maintainers of networkx at some point
        return deps

    def is_above(self, u_node: Image, v_node: Image) -> bool:
        """Test if one node is above another in the dependency tree."""
        return nx_has_path(self, u_node, v_node)

    def _is_valid_build_tuple(self, bt: tuple[Image]) -> bool:
        """Verify that all the dependencies of a build tuple can be met."""
        valid = True

        # check for similar images
        for i0 in range(len(bt)):
            for i2 in bt[i0 + 1 :]:
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
        """Create a build recipe."""
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


class ImageRepo(metaclass=OurMeta):
    """Image repository."""

    def __init__(self) -> None:
        self.images: set[Image] = set()
        # constraint(image, condition, type, spec, scope)
        self.constraints: list[tuple[str, str, str, str, str]] = list()
        if config.get("constraints", warn_on_miss=False) is not None:
            # arguments
            if "arguments" in config.get("constraints"):
                for argument in config.get("constraints")["arguments"]:
                    if isinstance(argument["value"], list):
                        specs = argument["value"]
                    else:
                        specs = [
                            argument["value"],
                        ]
                    for spec in specs:
                        self.constraints.append(
                            (
                                "",
                                argument["when"] if "when" in argument else "",
                                "argument",
                                spec,
                                "global",
                            )
                        )
            # variables
            if "variables" in config.get("constraints"):
                for variable in config.get("constraints")["variables"]:
                    self.constraints.append(
                        (
                            "",
                            variable["when"] if "when" in variable else "",
                            "variable",
                            "{}={}".format(variable["name"], variable["value"]),
                            "global",
                        )
                    )

    def import_from_dir(self, path: str) -> None:
        """Add Images from path."""
        p = Path(path)
        if not p.is_dir():
            raise NotADirectoryError(f"Image path {path} is not a directory!")

        for name in [x for x in p.iterdir() if x.is_dir() and x.name[0] != "."]:
            # check for duplicate image
            duplicate_image = False
            for _i in self.images:
                if _i.name == name.name:
                    duplicate_image = name
                    break
            if duplicate_image:
                logger.info("The image definition in '{}' is being skipped because it has the same name as an already imported image.".format(duplicate_image))
                continue

            # process metadata
            with open(name.joinpath("specs.yaml"), "r") as fi:
                specs_file = yaml_safe_load(fi)
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
                            name.name,
                            spec,
                            config.get("velocity:system"),
                            config.get("velocity:backend"),
                            config.get("velocity:distro"),
                            str(name),
                        )
                        if "when" in version:
                            if image.satisfies(version["when"]):
                                self.images.add(image)
                        else:
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
                            self.constraints.append(
                                (
                                    name.name,
                                    dependency["when"] if "when" in dependency else "",
                                    "dependency",
                                    spec,
                                    dependency["scope"] if "scope" in dependency else "image",
                                )
                            )
                # templates
                if "templates" in specs_file:
                    for template in specs_file["templates"]:
                        if isinstance(template["name"], list):
                            specs = template["name"]
                        else:
                            specs = [
                                template["name"],
                            ]
                        for spec in specs:
                            self.constraints.append(
                                (
                                    name.name,
                                    template["when"] if "when" in template else "",
                                    "template",
                                    spec,
                                    template["scope"] if "scope" in template else "image",
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
                                    name.name,
                                    argument["when"] if "when" in argument else "",
                                    "argument",
                                    spec,
                                    argument["scope"] if "scope" in argument else "image",
                                )
                            )
                # variables
                if "variables" in specs_file:
                    for variable in specs_file["variables"]:
                        self.constraints.append(
                            (
                                name.name,
                                variable["when"] if "when" in variable else "",
                                "variable",
                                "{}={}".format(variable["name"], variable["value"]),
                                variable["scope"] if "scope" in variable else "image",
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
                                    name.name,
                                    file["when"] if "when" in file else "",
                                    "file",
                                    spec,
                                    file["scope"] if "scope" in file else "image",
                                )
                            )
                # prologs
                if "prologs" in specs_file:
                    for prolog in specs_file["prologs"]:
                        self.constraints.append(
                            (
                                name.name,
                                prolog["when"] if "when" in prolog else "",
                                "prolog",
                                prolog["script"],
                                prolog["scope"] if "scope" in prolog else "image",
                            )
                        )

    def create_build_recipe(self, targets: list[str]) -> tuple[tuple, ImageGraph]:
        """Create an ordered build recipe of images."""
        images: set[Image] = deepcopy(self.images)

        build_targets: list[Target] = list()
        for target in targets:
            res = re_fullmatch(
                r"^(?P<name>[a-zA-Z0-9-]+)(?:(?:@(?P<left>[\d\.]+)(?!@))?(?:@?(?P<colen>:)(?P<right>[\d\.]+)?)?)?$",
                target,
            )
            if res is not None:
                gd: dict = res.groupdict()
                # n@v: or n@v
                if gd["left"] is not None and gd["right"] is None:
                    t = Image(
                        gd["name"],
                        gd["left"],
                        config.get("velocity:system"),
                        config.get("velocity:backend"),
                        config.get("velocity:distro"),
                        "",
                    )
                    if gd["colen"] is not None:
                        build_targets.append(Target(t, DepOp.GE))
                    else:
                        build_targets.append(Target(t, DepOp.EQ))
                # n@:v
                elif gd["left"] is None and gd["right"] is not None:
                    if gd["colen"] is not None:
                        t = Image(
                            gd["name"],
                            gd["right"],
                            config.get("velocity:system"),
                            config.get("velocity:backend"),
                            config.get("velocity:distro"),
                            "",
                        )
                        build_targets.append(Target(t, DepOp.LE))
                    else:
                        raise InvalidImageVersionError("Invalid version '{}'.".format(target))
                # n
                elif gd["left"] is None and gd["right"] is None:
                    if gd["colen"] is not None:
                        raise InvalidImageVersionError("Invalid version '{}'.".format(target))
                    else:
                        t = Image(
                            gd["name"],
                            "",
                            config.get("velocity:system"),
                            config.get("velocity:backend"),
                            config.get("velocity:distro"),
                            "",
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
                        "",
                    )
                    build_targets.append(Target(t, DepOp.GE))
                    t = Image(
                        gd["name"],
                        gd["right"],
                        config.get("velocity:system"),
                        config.get("velocity:backend"),
                        config.get("velocity:distro"),
                        "",
                    )
                    build_targets.append(Target(t, DepOp.LE))
            else:
                raise NoAvailableBuild("No available build!")

        # pre-burner graph
        for constraint in self.constraints:
            for image in images:
                if image.apply_constraint("{} {}".format(constraint[0], constraint[1]), constraint[2], constraint[3]):
                    images_changed = True
        ig = ImageGraph()
        for image in images:
            ig.add_node(image)
        for image in images:
            for dep in image.dependencies:
                for di in images:
                    if di.satisfies(dep):
                        ig.add_edge(image, di)

        bt: tuple[Image] = ig.create_build_recipe(build_targets)

        # apply constraints for the build scope
        images_changed: bool = True
        while images_changed:
            images_changed = False
            for constraint in self.constraints:
                if constraint[4] == "build":
                    for targ in bt:
                        if targ.satisfies(constraint[1]):
                            for image in images:
                                if image.apply_constraint(constraint[0], constraint[2], constraint[3]):
                                    images_changed = True
                # "image" or "universal"
                else:
                    for image in images:
                        if image.apply_constraint(
                            "{} {}".format(constraint[0], constraint[1]), constraint[2], constraint[3]
                        ):
                            images_changed = True

        # create graph
        ig = ImageGraph()
        for image in images:
            ig.add_node(image)
        for image in images:
            for dep in image.dependencies:
                for di in images:
                    if di.satisfies(dep):
                        ig.add_edge(image, di)

        bt: tuple[Image] = ig.create_build_recipe(build_targets)

        # update images so that their hash includes the layers below them
        cumulative_deps: int = 0
        for b in bt:
            b.underlay = cumulative_deps
            cumulative_deps = cumulative_deps + int(b.id, 16)

        bt_ig = ImageGraph()
        for image in bt:
            bt_ig.add_node(image)
        for image in bt:
            for dep in image.dependencies:
                for di in bt:
                    if di.satisfies(dep):
                        bt_ig.add_edge(image, di)

        return bt, bt_ig
