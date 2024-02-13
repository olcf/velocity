import os
import re
import yaml
import networkx as nx
from enum import Enum
from lib.exceptions import EdgeViolatesDAG, InvalidDependencySpecification, NoAvailableBuild
from lib.print import h1print, p1print, sp1print


def get_permutations(idx: int, sets: list[list]):
    """
    Get all the possible permutations from a list of lists
    :param idx:
    :param sets:
    :return:
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


class Node:
    """
    Node class for an image dependency graph. Uniquely identified by image name,
    host system, base image distro and image tag.
    """

    def __init__(self, name: str, system: str, distro: str, tag: str) -> None:
        self.name = name
        self.system = system
        self.distro = distro
        self.tag = tag

        # note that path is not considered when determining how two nodes compare to each other
        self.path = None

    def add_path(self, path: str) -> None:
        self.path = path

    def similar(self, other) -> bool:
        """
        compare two nodes solely on their name and tag
        :param other: node to compare with
        :return: true if the nodes share the same name and tag false otherwise
        """
        if (isinstance(other, Node) and self.name == other.name and
                self.system == other.system and self.distro == other.distro):
            return True
        else:
            return False

    def __eq__(self, other) -> bool:
        if (isinstance(other, Node) and self.name == other.name and self.system == other.system and
                self.distro == other.distro and self.tag == other.tag):
            return True
        else:
            return False

    def __gt__(self, other) -> bool:
        if (isinstance(other, Node) and self.name == other.name and self.system == other.system and
                self.distro == other.distro and self.tag > other.tag):
            return True
        else:
            return False

    def __ge__(self, other) -> bool:
        if (isinstance(other, Node) and self.name == other.name and self.system == other.system and
                self.distro == other.distro and self.tag >= other.tag):
            return True
        else:
            return False

    def __lt__(self, other) -> bool:
        if (isinstance(other, Node) and self.name == other.name and self.system == other.system and
                self.distro == other.distro and self.tag < other.tag):
            return True
        else:
            return False

    def __le__(self, other) -> bool:
        if (isinstance(other, Node) and self.name == other.name and self.system == other.system and
                self.distro == other.distro and self.tag <= other.tag):
            return True
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.name + self.system + self.distro + self.tag)

    def __str__(self) -> str:
        return f'Node({self.name}, {self.system}, {self.distro}, {self.tag})'


class DepOp(Enum):
    """
    Specify dependency options
    """
    EQ = '='
    GE = '^'
    LE = '_'
    UN = None


class Target:
    """
    Build specification targets
    """

    def __init__(self, node: Node, op: DepOp):
        self.node = node
        self.op = op

    def __str__(self):
        return f'Target: {self.op} -> {str(self.node)}'


class DependencyGraph(nx.DiGraph):

    def __init__(self, **attr) -> None:
        super().__init__(**attr)

    def load_from_directory(self, path) -> None:
        """
        load images from a specified directory
        :param path: path to load images from
        :return: None
        """
        if os.path.isdir(path):
            images = os.listdir(path)
            images.remove('README.md')
        else:
            raise NotADirectoryError(path)

        # add nodes to graph (dependencies are added later once all nodes are in the graph)
        for name in images:
            tags = os.listdir(f'{path}/{name}')
            for tag in tags:
                with open(f'{path}/{name}/{tag}/spec.yaml', 'r') as file:
                    spec = yaml.safe_load(file)
                    for system in spec['build_specs']:
                        for distro in spec['build_specs'][system]:
                            node = Node(name, system, distro, tag)
                            node.add_path(f'{path}/{name}/{tag}')
                            self.add_node(node)

        # add dependency edges to graph
        for name in images:
            tags = os.listdir(f'{path}/{name}')
            for tag in tags:
                with open(f'{path}/{name}/{tag}/spec.yaml', 'r') as file:
                    spec = yaml.safe_load(file)
                    for system in spec['build_specs']:
                        for distro in spec['build_specs'][system]:
                            if spec['build_specs'][system][distro] is not None:

                                for dependency in spec['build_specs'][system][distro]:
                                    if dependency is None:
                                        raise InvalidDependencySpecification(dependency, name, tag,
                                                                             f'{path}/{name}/{tag}/spec.yaml')
                                    else:
                                        # split up specification into parts
                                        result = re.search(r'^(.*)@(.*)([%^_=])(.*)$', dependency)

                                    # add the specified edge(s) to the graph
                                    if result is not None:
                                        if result[3] == '=':
                                            self.add_edge(Node(name, system, distro, tag),
                                                          Node(result[1], system, distro, result[4]))
                                        elif result[3] == '^':
                                            for n in self.nodes:
                                                if n >= Node(result[1], system, distro, result[4]):
                                                    self.add_edge(Node(name, system, distro, tag), n)
                                        elif result[3] == '_':
                                            for n in self.nodes:
                                                if n <= Node(result[1], system, distro, result[4]):
                                                    self.add_edge(Node(name, system, distro, tag), n)
                                        elif result[3] == '%':
                                            for n in self.nodes:
                                                if (Node(result[1], system, distro, result[2]) <= n
                                                        <= Node(result[1], system, distro, result[4])):
                                                    self.add_edge(Node(name, system, distro, tag), n)
                                    else:
                                        for n in self.nodes:
                                            if n.similar(Node(dependency, system, distro, '')):
                                                self.add_edge(Node(name, system, distro, tag), n)

    def add_edge(self, u_of_edge, v_of_edge, **attr):
        super().add_edge(u_of_edge, v_of_edge, **attr)

        if not self._is_dag():
            cycle = nx.find_cycle(self)
            raise EdgeViolatesDAG(u_of_edge, v_of_edge, cycle)

    def _is_dag(self) -> bool:
        return nx.is_directed_acyclic_graph(self)

    def get_similar_nodes(self, node: Node) -> set:
        similar = set()
        for n in self.nodes:
            if n.similar(node):
                similar.add(n)
        return similar

    def get_dependencies(self, node: Node):
        return nx.neighbors(self, node)

    def is_above(self, u_node: Node, v_node: Node) -> bool:
        """
        Test if one node is above another in the dependency tree
        """
        return nx.has_path(self, u_node, v_node)

    def _is_valid_build_tuple(self, bt: tuple[Node]) -> bool:
        """
        Verify that all the dependencies of a build tuple can be met.
        """
        valid = True

        # check for similar images
        for i0 in range(len(bt)):
            for i2 in bt[i0 + 1:]:
                if bt[i0].similar(i2):
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

    def create_build_recipe(self, targets: list[Target]):
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
                if node.similar(target.node):
                    if target.op == DepOp.EQ and node != target.node:
                        build_set.remove(node)
                    elif target.op == DepOp.GE and node < target.node:
                        build_set.remove(node)
                    elif target.op == DepOp.LE and node > target.node:
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
            if self._is_valid_build_tuple(tuple(p)):
                # order build
                build_list = list()
                processed = set()
                unprocessed = p
                while len(unprocessed) > 0:
                    for node in unprocessed.copy():
                        deps = set(self.get_dependencies(node)).intersection(p)
                        if deps.issubset(processed):
                            processed.add(node)
                            unprocessed.remove(node)
                            build_list.append(node)

                return tuple(build_list)

        # if we got here no valid build tuple could be found
        raise NoAvailableBuild

    def print_avail(self) -> None:
        h1print("AVAILABLE IMAGES")

        # group and order
        grouped = dict()
        for node in self.nodes:
            if node.name not in grouped:
                grouped[node.name] = list()
            grouped[node.name].append(node)
        ordered = list(grouped.keys())
        ordered.sort()

        # print
        for group in ordered:
            p1print(group)
            tmp = grouped[group]
            tmp.sort()
            for t in tmp:
                sp1print(t.tag)
