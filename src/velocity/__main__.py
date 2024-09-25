"""Run velocity as a script."""

import argparse
import sys
from loguru import logger
from importlib.metadata import version
from colorama import Fore, Style
from ._graph import ImageRepo, Image
from ._build import ImageBuilder
from ._print import header_print, indent_print, TextBlock, bare_print
from ._config import config

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
    "-D",
    "--debug",
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
    "-l", "--leave-tags", action="store_true", help="do not clean up intermediate build tags (only applies to podman)"
)
build_parser.add_argument("-v", "--verbose", action="store_true", help="print helpful debug/runtime information")
build_parser.add_argument("-c", "--clean", action="store_true", help="run clean build (delete cached builds)")

# create avail_parser
avail_parser = sub_parsers.add_parser("avail", help="lookup available images")

# create spec_parser
spec_parser = sub_parsers.add_parser("spec", help="lookup image dependencies")
spec_parser.add_argument("targets", type=str, nargs="+", help="spec targets")

# parse args
args = parser.parse_args()

############################################################
# apply user run time arguments over settings
############################################################
if args.debug is not None:
    config.set("velocity:debug", args.debug)
if args.system is not None:
    config.set("velocity:system", args.system)
if args.backend is not None:
    config.set("velocity:backend", args.backend)
if args.distro is not None:
    config.set("velocity:distro", args.distro)

# setup logging and log startup
logger.enable("velocity")
logger.configure(handlers=[{"sink": sys.stdout, "level": config.get("velocity:debug")}])
logger.debug(
    "Starting velocity {},{},{}.".format(
        config.get("velocity:system"), config.get("velocity:backend"), config.get("velocity:distro")
    )
)
logger.trace(config.get(""))

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
    ordered = list(grouped.keys())
    ordered.sort()

    # print
    for group in ordered:
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
