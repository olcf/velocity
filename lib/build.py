import random
import shutil
import os
import subprocess
import string
from pathlib import Path
from colorama import Fore, Style
from lib.graph import Node
from lib.print import p1print, sp1print, TextBlock
from lib.exceptions import BackendNotSupported
from lib.template import parse_template


def run(cmd: str):
    """
    Has ability to capture output but not currently used.
    """
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        elif output != '':
            print(output.strip('\n'))
    if process.poll() != 0:
        exit(process.poll())


class BuildUnit:

    def __init__(self, node: Node):
        self.node = node
        self.build_id = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))


class Builder:

    def __init__(self, bt: tuple[Node], backend: str, system: str, distro: str, build_dir: str,
                 build_name: str = None, dry_run: bool = False, leave_tags: bool = True):
        self.build_units = list()
        self.backend = backend
        self.system = system
        self.distro = distro
        self.build_dir = Path(build_dir)
        self.build_name = build_name
        self.dry_run = dry_run
        self.leave_tags = leave_tags

        # create build_dir if it does not exist
        self.build_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        for node in bt:
            self.build_units.append(BuildUnit(node))

    def build(self):
        # store pwd
        pwd = Path(Path().absolute())

        # clear build_dir
        for entry in self.build_dir.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()

        last = None     # last image that was built
        for u in self.build_units:
            if self.backend == 'podman':
                if u == self.build_units[-1]:   # if this is the last image
                    name = str(self.build_name if self.build_name is not None else
                               f'{u.node.name}__{u.node.tag}__{self.system}__{self.distro}')
                    if '/' not in name and ':' not in name:
                        name = f'localhost/{name}:latest'
                else:
                    name = f'localhost/{u.build_id}:latest'
            elif self.backend == 'apptainer':
                if u == self.build_units[-1]:   # if this is the last image
                    name = str(Path.joinpath(pwd.absolute(),
                                             self.build_name if self.build_name is not None else
                                             f'{u.node.name}__{u.node.tag}__{self.system}__{self.distro}'))
                    if '.sif' not in name:
                        name += '.sif'
                else:
                    name = str(Path.joinpath(self.build_dir, u.build_id, f'{u.build_id}.sif'))
            else:
                raise BackendNotSupported

            self._build_image(u, last, name)
            if self.backend == 'podman' and not self.dry_run and not self.leave_tags and last is not None:
                run(f'podman untag {last}')
            last = name

        # go back to the starting dir
        os.chdir(pwd)

    def _build_image(self, unit: BuildUnit, src_image: str, name: str):
        # print start of build
        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": BUILD "),
            TextBlock(f"{unit.node.name}@={unit.node.tag}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(f"{' --DRY-RUN' if self.dry_run else ''} ...")
        ])

        # create build dir and go to it
        build_sub_dir = Path.joinpath(self.build_dir, unit.build_id)
        build_sub_dir.mkdir(mode=0o744)
        os.chdir(build_sub_dir)

        # copy additional files
        if Path.joinpath(unit.node.path, self.system).is_dir():
            p1print([
                TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": COPYING FILES ...")
            ])

            for entry in Path.joinpath(unit.node.path, self.system).iterdir():
                # print copy operation
                sp1print([
                    TextBlock('DIR: ' if entry.is_dir() else 'FILE: ', fore=Fore.YELLOW, style=Style.BRIGHT),
                    TextBlock(f"{entry.absolute()}", fore=Fore.GREEN),
                    TextBlock(f" -> ", fore=Fore.YELLOW, style=Style.BRIGHT),
                    TextBlock(f"{Path.joinpath(build_sub_dir, entry.name).absolute()}", fore=Fore.GREEN)
                ])
                if entry.is_dir():
                    shutil.copytree(entry, Path.joinpath(build_sub_dir, entry.name))
                else:
                    shutil.copy(entry, Path.joinpath(build_sub_dir, entry.name))

        # parse template and create script
        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": GENERATING SCRIPT ...")
        ])
        sp1print([
            TextBlock('SCRIPT: ', fore=Fore.YELLOW, style=Style.BRIGHT),
            TextBlock(f"{Path.joinpath(build_sub_dir, f'{unit.build_id}.script')}", fore=Fore.GREEN)
        ])
        # get and update script variables
        script_variables = unit.node.build_specifications['variables'] if 'variables' in unit.node.build_specifications else dict()
        if src_image is not None:
            script_variables.update({'image': src_image})
        # load template
        with open(Path.joinpath(unit.node.path, 'templates', f'{self.distro}.vtmp'), 'r') as in_file:
            script = parse_template(in_file, self.backend, script_variables)
        # write out script
        with open(Path.joinpath(build_sub_dir, f'{unit.build_id}.script'), 'w') as out_file:
            for line in script:
                sp1print([
                    TextBlock(line, fore=Fore.CYAN, style=Style.BRIGHT)
                ])
                out_file.writelines(line + '\n')

        # diverge for backend
        if self.backend == 'podman':
            # run prolog for podman build
            if 'prolog' in unit.node.build_specifications:
                p1print([
                    TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                    TextBlock(f": RUNNING PROLOG ...")
                ])
                if not self.dry_run:
                    prolog = Path.joinpath(build_sub_dir, unit.node.build_specifications['prolog'])
                    prolog.chmod(0o744)
                    run(str(prolog.absolute()))

            # build
            p1print([
                TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": BUILDING ...")
            ])

            args = ' ' + ' '.join(
                _ for _ in unit.node.build_specifications['arguments']) if 'arguments' in unit.node.build_specifications else ''
            script = f' -f {Path.joinpath(build_sub_dir, f"{unit.build_id}.script")}'
            destination = f' -t {name}'
            end = ' .;'

            cmd = ['podman build', args, script, destination, end]
            sp1print([
                TextBlock(''.join(_ for _ in cmd), fore=Fore.YELLOW, style=Style.BRIGHT)
            ])
            if not self.dry_run:
                run(''.join(_ for _ in cmd))

        elif self.backend == 'apptainer':
            # no prolog needed for apptainer build

            # build
            p1print([
                TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": BUILDING ...")
            ])

            args = ' ' + ' '.join(
                x for x in unit.node.build_specifications['arguments']) if 'arguments' in unit.node.build_specifications else ''
            script = f' {Path.joinpath(build_sub_dir, f"{unit.build_id}.script")}'
            destination = f' {name}'
            end = ';'

            cmd = ['apptainer build', args, destination, script, end]
            sp1print([
                TextBlock(''.join(_ for _ in cmd), fore=Fore.YELLOW, style=Style.BRIGHT)
            ])
            if not self.dry_run:
                run(''.join(_ for _ in cmd))

        else:
            raise BackendNotSupported(self.backend)

        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": IMAGE "),
            TextBlock(f"{name}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(' ('),
            TextBlock(f"{unit.node.name}@={unit.node.tag}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(')'),
            TextBlock(f" BUILT")
        ])
        print()
