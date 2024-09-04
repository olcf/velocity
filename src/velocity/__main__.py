import argparse
import re
import os
import editor
from pathlib import Path
from colorama import Fore, Style
from ._graph import ImageRepo, Target, DepOp
from ._build import Builder
from ._print import p1print, sp1print, TextBlock, wprint, print_text_blocks
from ._config import config


############################################################
# Main
############################################################
if __name__ == '__main__':

    ############################################################
    # Load Config
    ############################################################
    if os.getenv('VELOCITY_SYSTEM') is not None:
        config.set("velocity:system", os.getenv('VELOCITY_SYSTEM'))
    if os.getenv('VELOCITY_BACKEND') is not None:
        config.set("velocity:backend", os.getenv('VELOCITY_BACKEND'))
    if os.getenv('VELOCITY_DISTRO') is not None:
        config.set("velocity:distro", os.getenv('VELOCITY_DISTRO'))
    if os.getenv('VELOCITY_BUILD_DIR') is not None:
        config.set("velocity:build_dir", os.getenv('VELOCITY_BUILD_DIR'))

    ############################################################
    # Parse Args
    ############################################################
    parser = argparse.ArgumentParser(
        prog='velocity',
        description='Build tool for OLCF containers',
        epilog='See (https://gitlab.ccs.ornl.gov/saue-software/velocity)')
    parser.add_argument('-v', '--version', action='version',
                        version=f"%(prog)s {config.get('velocity:version')}", help="program version")
    parser.add_argument('-b', '--backend', action='store')
    parser.add_argument('-s', '--system', action='store')
    parser.add_argument('-d', '--distro', action='store')

    # create sub_parsers
    sub_parsers = parser.add_subparsers(dest='subcommand')

    # create build_parser
    build_parser = sub_parsers.add_parser('build', help="build specified container image")
    build_parser.add_argument('-d', '--dry-run', action='store_true', help="dry run build system")
    build_parser.add_argument('targets', type=str, nargs='+', help='build targets')
    build_parser.add_argument('-n', '--name', action='store', help='name of complete image')
    build_parser.add_argument('-l', '--leave-tags', action='store_true',
                              help="do not clean up intermediate build tags (only applies to podman)")
    build_parser.add_argument('-v', '--verbose', action='store_true', help="print helpful debug/runtime information")

    # create avail_parser
    avail_parser = sub_parsers.add_parser('avail', help="lookup available images")

    # create spec_parser
    spec_parser = sub_parsers.add_parser('spec', help="lookup image dependencies")
    spec_parser.add_argument('targets', type=str, nargs='+', help='spec targets')

    # create edit_parser
    edit_parser = sub_parsers.add_parser('edit', help="edit image files")
    edit_parser.add_argument('target', help='image to edit')
    edit_parser.add_argument('-s', '--specification', action='store_true', help="edit the specifications file")

    # create create_parser
    edit_parser = sub_parsers.add_parser('create', help="create a new image with default template")
    edit_parser.add_argument('name', help='name of image to create')
    edit_parser.add_argument('version', help='version of image to create')

    # parse args
    args = parser.parse_args()

    ############################################################
    # apply user run time arguments over settings
    ############################################################
    if args.system is not None:
        config.set("velocity:system", args.system)
    if args.backend is not None:
        config.set("velocity:backend", args.backend)
    if args.distro is not None:
        config.set("velocity:distro", args.distro)

    ############################################################
    # Load images
    ############################################################
    imageRepo = ImageRepo()
    imageRepo.import_from_dir("/home/xjv/PycharmProjects/velocity-images")

    # print backend, system, distro
    """
    p1print([
        TextBlock(f"System: "),
        TextBlock(f"{SETTINGS['VELOCITY_SYSTEM']}", fore=Fore.MAGENTA, style=Style.BRIGHT)
    ])
    p1print([
        TextBlock(f"Backend: "),
        TextBlock(f"{SETTINGS['VELOCITY_BACKEND']}", fore=Fore.MAGENTA, style=Style.BRIGHT)
    ])
    p1print([
        TextBlock(f"Distro: "),
        TextBlock(f"{SETTINGS['VELOCITY_DISTRO']}", fore=Fore.MAGENTA, style=Style.BRIGHT)
    ])
    print()  # add newline
    """

    ############################################################
    # Handle User Commands
    ############################################################
    if args.subcommand == 'build':
        # parse targets

        # get recipe
        recipe = imageRepo.create_build_recipe(args.targets)

        # print build specs
        p1print([
            TextBlock('Build Order:')
        ])
        for r in recipe:
            sp1print([
                TextBlock(f"{r.name}@{r.version}", fore=Fore.MAGENTA, style=Style.BRIGHT)
            ])
        print()  # add newline

        # prep builder
        builder = Builder(
            recipe,
            build_name=args.name,
            dry_run=args.dry_run,
            leave_tags=args.leave_tags,
            verbose=args.verbose
        )

        # build
        builder.build()

    elif args.subcommand == 'avail':

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
            p1print([
                TextBlock(group, fore=Fore.RED, style=Style.BRIGHT)
            ])
            deps = grouped[group]
            deps.sort()
            for t in deps:
                sp1print([
                    TextBlock(t.version, fore=Fore.YELLOW, style=Style.BRIGHT)
                ])
        print()  # add newline

    elif args.subcommand == 'spec':
        # parse targets
        targets = []
        for target in args.targets:
            result = re.search(r'^(.*)@(.*)([%^_=])(.*)$', target)
            if result is not None:
                if result[3] == '=':
                    targets.append(Target(Node(result[1], result[4]), DepOp.EQ))
                elif result[3] == '^':
                    targets.append(Target(Node(result[1], result[4]), DepOp.GE))
                elif result[3] == '_':
                    targets.append(Target(Node(result[1], result[4]), DepOp.LE))
                elif result[3] == '%':
                    targets.append(Target(Node(result[1], result[2]), DepOp.GE))
                    targets.append(Target(Node(result[1], result[4]), DepOp.LE))
            else:
                targets.append(Target(Node(target, ''), DepOp.UN))

        # get recipe
        recipe = imageGraph.create_build_recipe(targets)

        # flatten dependency tree
        flat_dep_tree = dict()
        for r in recipe:
            flat_dep_tree[r.name] = set()
            deps = set(imageGraph.get_dependencies(r))
            for o in deps.intersection(set(recipe)):
                flat_dep_tree[r.name].add(o.name)
        # get top level entries
        top_level_entries = set()
        deps = set()
        for r in recipe:
            deps.update(imageGraph.get_dependencies(r))
        for r in recipe:
            if r not in deps:
                top_level_entries.add(r)


        def spec_print(seed: str, indent: int, fdt: dict, rs: tuple[Node]):
            """
            Recursive function to print dep tree
            """
            spec = None
            for _ in rs:
                if _.similar(Node(seed, '')):
                    spec = f"{_.name}@={_.tag}"
            print('  ' + '   ' * indent, end='')
            if indent == 0:
                print_text_blocks([
                    TextBlock('> ', fore=Fore.RED, style=Style.BRIGHT),
                    TextBlock(spec, fore=Fore.MAGENTA, style=Style.BRIGHT)
                ])
            else:
                print_text_blocks([
                    TextBlock('^', fore=Fore.GREEN, style=Style.BRIGHT),
                    TextBlock(spec, fore=Fore.MAGENTA, style=Style.BRIGHT)
                ])
            if len(fdt[seed]) > 0:
                for un in fdt[seed]:
                    spec_print(un, (indent + 1), fdt, rs)


        # print specs
        for tl in top_level_entries:
            spec_print(tl.name, 0, flat_dep_tree, recipe)
        print()  # add newline

    elif args.subcommand == 'edit':

        name = None
        tag = None
        result = re.search(r'^(.*)@=(.*)$', args.target)
        if result:
            name = Path(SETTINGS['VELOCITY_IMAGE_DIR']).joinpath(result[1])
            tag = Path.joinpath(name, result[2])
        else:
            name = Path(SETTINGS['VELOCITY_IMAGE_DIR']).joinpath(args.target)

        if name.is_dir():
            if tag is None:
                tags = list(name.iterdir())
                tags.sort()
                tag = Path.joinpath(name, tags[-1])

            if tag.is_dir():
                if args.specification:
                    file = Path.joinpath(tag, 'specifications.yaml')
                else:
                    file = Path.joinpath(tag, 'templates', f"{SETTINGS['VELOCITY_DISTRO']}.vtmp")

                if file.is_file():
                    editor.edit(file)
                else:
                    raise FileNotFoundError(file)
            else:
                raise NotADirectoryError(tag)
        else:
            raise NotADirectoryError(name)

    elif args.subcommand == 'create':
        image_dir = Path(SETTINGS['VELOCITY_IMAGE_DIR']).joinpath(args.name, args.version)
        if image_dir.is_dir():
            raise FileExistsError(f"'{image_dir}' already exist!")
        os.mkdir(image_dir)
        os.mkdir(image_dir.joinpath('templates'))
        with open(image_dir.joinpath('specifications.yaml'), 'w') as spec_file:
            spec_file.write('---\n')
            spec_file.write('\n')
            spec_file.write('build_specifications:\n')
            spec_file.write(f"  {SETTINGS['VELOCITY_SYSTEM']}:\n")
            spec_file.write(f"    {SETTINGS['VELOCITY_BACKEND']}:\n")
            spec_file.write(f"      {SETTINGS['VELOCITY_DISTRO']}: {{}}\n")
        with open(image_dir.joinpath('templates', f"{SETTINGS['VELOCITY_DISTRO']}.vtmp"), 'x') as temp_file:
            temp_file.write('\n')
            temp_file.write('@from\n')
            temp_file.write('    %(__base__)\n')
            temp_file.write('\n')
            temp_file.write('@label\n')
            temp_file.write('    velocity.image.%(__name__)__%(__tag__) %(__hash__)\n')

    else:
        parser.print_help()
        print()  # add newline