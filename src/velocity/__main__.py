"""Run velocity as a script."""

import argparse
import sys
from loguru import logger
from importlib.metadata import version
from colorama import Fore, Style
from ._graph import ImageRepo, Image
from ._build import ImageBuilder
from ._print import header_print, indent_print, TextBlock, bare_print
from re import fullmatch as re_fullmatch
from ._config import config
from._exceptions import InvalidCLIArgumentFormat

############################################################
# Parse Args
############################################################
parser = argparse.ArgumentParser(
    prog="velocity",
    description="build tool for OLCF containers",
    epilog="See https://github.com/olcf/velocity",
)
parser.add_argument(
    "-v", "--version", action="version", version=f"%(prog)s {version('olcf-velocity')}", help="program version"
)
parser.add_argument(
    "-L",
    "--logging-level",
    choices=["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
    help="set debug output level",
)
parser.add_argument("-b", "--backend")
parser.add_argument("-s", "--system")
parser.add_argument("-d", "--distro")

# create sub_parsers
sub_parsers = parser.add_subparsers(dest="subcommand")

# create build_parser
build_parser = sub_parsers.add_parser("build", help="build specified container image")
build_parser.add_argument("-d", "--dry-run", action="store_true", help="dry run build system")
build_parser.add_argument("targets", type=str, nargs="+", help="build targets")
build_parser.add_argument("-n", "--name", action="store", help="name of complete image")
build_parser.add_argument(
    "-l", "--leave-tags", action="store_true", help="do not clean up intermediate build tags (only applies to dockerish backends)"
)
build_parser.add_argument("-v", "--verbose", action="store_true", help="print helpful debug/runtime information")
build_parser.add_argument("-c", "--clean", action="store_true", help="run clean build (delete cached builds)")
build_parser.add_argument("-A", "--argument", action="append", dest="arguments", default=list(),
                          help='define an argument (e.g -A "value: --disable-cache; when: backend=apptainer")')
build_parser.add_argument("-V", "--variable", action="append", dest="variables", default=list(),
                          help='define a variable (e.g -V "name: example; value: 1234")')

# create avail_parser
avail_parser = sub_parsers.add_parser("avail", help="lookup available images")
avail_parser.add_argument("targets", type=str, nargs="*", help="build targets")

# create spec_parser
spec_parser = sub_parsers.add_parser("spec", help="lookup image dependencies")
spec_parser.add_argument("targets", type=str, nargs="+", help="spec targets")

# parse args
args = parser.parse_args()

# parse arguments & variables
if "argument" in args:
    for argument in args.arguments:
        try:
            constructed_arg: dict = dict()
            a_split: list = argument.split(";")
            for a_item in a_split:
                parts: dict = re_fullmatch(r"^\s*(?P<key>\S+)\s*:\s*(?P<value>\S+)\s*$", a_item).groupdict()
                constructed_arg[parts["key"]] = parts["value"]
            prev_arguments: list | None = config.get("constraints:arguments", warn_on_miss=False)
            if prev_arguments is None:
                config.set("constraints:arguments", [constructed_arg, ])
            else:
                prev_arguments.append(constructed_arg)
                config.set("constraints:arguments", prev_arguments)
        except AttributeError:
            raise InvalidCLIArgumentFormat("Invalid format in '{}'".format(argument))
if "variables" in args:
    for variable in args.variables:
        try:
            constructed_var: dict = dict()
            v_split: list = variable.split(";")
            for v_item in v_split:
                parts: dict = re_fullmatch(r"^\s*(?P<key>\S+)\s*:\s*(?P<value>\S+)\s*$", v_item).groupdict()
                constructed_var[parts["key"]] = parts["value"]
            prev_variables: list | None = config.get("constraints:variables", warn_on_miss=False)
            if prev_variables is None:
                config.set("constraints:variables", [constructed_var, ])
            else:
                prev_variables.append(constructed_var)
                config.set("constraints:variables", prev_variables)
        except AttributeError:
            raise InvalidCLIArgumentFormat("Invalid format in '{}'".format(variable))

############################################################
# apply user run time arguments over settings
############################################################
if args.logging_level is not None:
    config.set("velocity:logging:level", args.logging_level)
if args.system is not None:
    config.set("velocity:system", args.system)
if args.backend is not None:
    config.set("velocity:backend", args.backend)
if args.distro is not None:
    config.set("velocity:distro", args.distro)

# setup logging and log startup
logger.enable("velocity")
logger.configure(handlers=[{"sink": sys.stdout, "level": config.get("velocity:logging:level")}])
logger.debug("Starting velocity.")
logger.debug(config.get(""))

############################################################
# Load images
############################################################
imageRepo = ImageRepo()
for p in config.get("velocity:image_path").strip(":").split(":"):
    imageRepo.import_from_dir(p)

############################################################
# Handle User Commands
############################################################
if args.subcommand == "build":
    # get recipe
    recipe = imageRepo.create_build_recipe(args.targets)[0]

    # print build specs
    header_print([TextBlock("Build Order:")])
    for r in recipe:
        indent_print([TextBlock(f"{r.name}@{r.version}-{r.id}", fore=Fore.MAGENTA, style=Style.BRIGHT)])
    print()  # newline

    # prep builder
    builder = ImageBuilder(
        recipe,
        build_name=args.name,
        dry_run=args.dry_run,
        remove_tags=not args.leave_tags,
        verbose=args.verbose,
        clean_build_dir=args.clean
    )

    # build
    builder.build()

elif args.subcommand == "avail":
    # group and order
    grouped = dict()
    for node in imageRepo.images:
        if node.name not in grouped:
            grouped[node.name] = list()
        grouped[node.name].append(node)

    relevant_images: list = list(grouped.keys())
    if len(args.targets) > 0:
        relevant_images = list(filter(lambda x: x in args.targets, relevant_images))
    relevant_images.sort()

    # print
    for group in relevant_images:
        header_print([TextBlock(group, fore=Fore.RED, style=Style.BRIGHT)])
        deps = grouped[group]
        deps.sort()
        for t in deps:
            indent_print([TextBlock(t.version, fore=Fore.YELLOW, style=Style.BRIGHT)])
    print()  # add newline

elif args.subcommand == "spec":
    # get recipe
    recipe, graph = imageRepo.create_build_recipe(args.targets)

    # flatten dependency tree
    flat_dep_tree = dict()
    for r in recipe:
        flat_dep_tree[r.name] = set()
        deps = set(graph.get_dependencies(r))
        for o in deps.intersection(set(recipe)):
            flat_dep_tree[r.name].add(o.name)
    # get top level entries
    top_level_entries = set()
    deps = set()
    for r in recipe:
        deps.update(graph.get_dependencies(r))
    for r in recipe:
        if r not in deps:
            top_level_entries.add(r)

    def spec_print(seed: str, indent: int, fdt: dict, rs: tuple[Image]):
        """
        Recursive function to print dep tree
        """
        spec = ""
        for _ in rs:
            if _.satisfies(seed):
                spec = "{}@{}-{}".format(_.name, _.version, _.id)
        print("  " + "   " * indent, end="")
        if indent == 0:
            bare_print(
                [
                    TextBlock("> ", fore=Fore.RED, style=Style.BRIGHT),
                    TextBlock(spec, fore=Fore.MAGENTA, style=Style.BRIGHT),
                ]
            )
        else:
            bare_print(
                [
                    TextBlock("^", fore=Fore.GREEN, style=Style.BRIGHT),
                    TextBlock(spec, fore=Fore.MAGENTA, style=Style.BRIGHT),
                ]
            )
        if len(fdt[seed]) > 0:
            for un in fdt[seed]:
                spec_print(un, (indent + 1), fdt, rs)

    # print specs
    for tl in top_level_entries:
        spec_print(tl.name, 0, flat_dep_tree, recipe)
    print()  # add newline
else:
    parser.print_help()
    print()  # add newline
