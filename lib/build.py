import datetime
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
from lib.backends import get_backend


def run(cmd: str, verbose: bool = False):
    """
    Has ability to capture output but not currently used.
    """
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        elif output != '' and verbose:
            sp1print([
                TextBlock(output.strip('\n'), fore=Fore.GREEN, style=Style.DIM)
            ])
    if process.poll() != 0:
        for line in process.stderr.readlines():
            sp1print([
                TextBlock(line.strip('\n'), fore=Fore.RED, style=Style.BRIGHT)
            ])
        exit(process.poll())


class BuildUnit:

    def __init__(self, node: Node):
        self.node = node
        self.build_id = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))


class Builder:

    def __init__(self, bt: tuple[Node], backend: str, system: str, distro: str, build_dir: str,
                 build_name: str = None, dry_run: bool = False, leave_tags: bool = True, verbose: bool = False):
        self.build_units = list()
        self.backend = backend
        self.system = system
        self.distro = distro
        self.build_dir = Path(build_dir)
        self.build_name = build_name
        self.dry_run = dry_run
        self.leave_tags = leave_tags
        self.verbose = verbose

        self.backend_engine = get_backend(self.backend, {'__system__': self.system, '__distro__': self.distro})

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

        # run prolog
        if 'prolog' in unit.node.build_specifications:
            p1print([
                TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": RUNNING PROLOG ...")
            ])
            if not self.dry_run:
                prolog = Path.joinpath(build_sub_dir, unit.node.build_specifications['prolog'])
                prolog.chmod(0o744)
                run(str(prolog.absolute()), verbose=self.verbose)

        # parse template and create script...
        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": GENERATING SCRIPT ...")
        ])
        sp1print([
            TextBlock('SCRIPT: ', fore=Fore.YELLOW, style=Style.BRIGHT),
            TextBlock(f"{Path.joinpath(build_sub_dir, f'{unit.build_id}.script')}", fore=Fore.GREEN)
        ])

        # get and update script variables
        script_variables = unit.node.build_specifications['variables'] \
            if 'variables' in unit.node.build_specifications else dict()
        script_variables.update({'__name__': unit.node.name})
        script_variables.update({'__tag__': unit.node.tag})
        script_variables.update({'__timestamp__': datetime.datetime.now()})
        if src_image is not None:
            script_variables.update({'__image__': src_image})

        script = self.backend_engine.generate_script(
            Path.joinpath(unit.node.path, 'templates', f'{self.distro}.vtmp'),
            script_variables
        )
        # write out script
        with open(Path.joinpath(build_sub_dir, f'{unit.build_id}.script'), 'w') as out_file:
            for line in script:
                if self.verbose:
                    sp1print([
                        TextBlock(line, fore=Fore.BLUE, style=Style.DIM)
                    ])
                out_file.writelines(line + '\n')

        # build
        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": BUILDING ...")
        ])

        build_cmd = self.backend_engine.generate_build_cmd(
            str(Path.joinpath(build_sub_dir, f"{unit.build_id}.script")),
            name,
            unit.node.build_specifications['arguments'] if 'arguments' in unit.node.build_specifications else None
        )

        sp1print([
            TextBlock(build_cmd, fore=Fore.YELLOW, style=Style.BRIGHT)
        ])
        if not self.dry_run:
            run(build_cmd, verbose=self.verbose)

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
