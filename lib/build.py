import random
import shutil
import os
import subprocess
import string
from enum import Enum
from pathlib import Path
from colorama import Fore, Style
from lib.graph import Node
from lib.print import p1print, sp1print, TextBlock
from lib.exceptions import BackendNotSupported


def run(cmd: str):
    print(Fore.CYAN, end='')
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        elif output != '':
            print(output.strip('\n'))
    if process.poll() != 0:
        exit(process.poll())
    print(Style.RESET_ALL, end='')


class Podman(Enum):
    SCRIP_EX = 'Dockerfile'
    BUILD_CMD = 'podman build'


class Apptainer(Enum):
    SCRIP_EX = 'def'
    BUILD_CMD = 'apptainer build'


class BuildUnit:

    def __init__(self, node: Node):
        self.node = node
        self.build_id = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))


class Builder:

    def __init__(self, bt: tuple[Node], backend, system, distro, build_dir,
                 build_name=None, dry_run=False, leave_tags=True):
        self.build_units = list()
        self.backend = backend
        self.system = system
        self.distro = distro
        self.build_dir = Path(build_dir)
        self.build_name = build_name
        self.dry_run = dry_run
        self.leave_tags = leave_tags

        self.build_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        for node in bt:
            self.build_units.append(BuildUnit(node))

    def build(self):
        pwd = Path(Path().absolute())

        for entry in self.build_dir.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()

        last = str()
        for u in self.build_units:
            if self.backend == 'podman':
                if u == self.build_units[-1]:
                    name = str(self.build_name if self.build_name is not None else u.build_id)
                else:
                    name = f'localhost/{u.build_id}:latest'
                if not self.dry_run and not self.leave_tags and last != '':
                    run(f'podman untag {last}')
            elif self.backend == 'apptainer':
                if u == self.build_units[-1]:
                    name = str(Path.joinpath(pwd.absolute(), self.build_name if self.build_name is not None else u.build_id))
                    if '.sif' not in name:
                        name += '.sif'
                else:
                    name = str(Path.joinpath(self.build_dir, u.build_id, f'{u.build_id}.sif'))
            else:
                raise BackendNotSupported

            self._build_image(u, last, name)
            last = name

        os.chdir(pwd)

    def _build_image(self, unit: BuildUnit, source: str, name: str):
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

        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": COPYING FILES ...")
        ])
        # copy additional files
        if Path.joinpath(unit.node.path, self.system).is_dir():

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

        # diverge for backend
        if self.backend == 'podman':
            # copy script
            sp1print([
                TextBlock('SCRIPT: ', fore=Fore.YELLOW, style=Style.BRIGHT),
                TextBlock(
                    f"{Path.joinpath(unit.node.path, 'build_scripts', f'{self.distro}.{Podman.SCRIP_EX.value}')}",
                    fore=Fore.GREEN),
                TextBlock(f" -> ", fore=Fore.YELLOW, style=Style.BRIGHT),
                TextBlock(f"{Path.joinpath(build_sub_dir, f'{unit.build_id}.{Podman.SCRIP_EX.value}')}", fore=Fore.GREEN)
            ])
            if not self.dry_run:
                shutil.copy(Path.joinpath(unit.node.path, 'build_scripts', f'{self.distro}.{Podman.SCRIP_EX.value}'),
                            Path.joinpath(build_sub_dir, f'{unit.build_id}.{Podman.SCRIP_EX.value}'))

            # run prolog for podman build
            if 'prolog' in unit.node.build_spec:
                p1print([
                    TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                    TextBlock(f": RUNNING PROLOG ...")
                ])
                if not self.dry_run:
                    prolog = Path.joinpath(build_sub_dir, unit.node.build_spec['prolog'])
                    prolog.chmod(0o744)
                    run(str(prolog.absolute()))

            # build
            p1print([
                TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": BUILDING ...")
            ])
            build_args = ' '.join(_ for _ in unit.node.build_spec['build_args']) if 'build_args' in unit.node.build_spec else ''
            IMAGE = f'--build-arg IMAGE={source}'
            script = f'-f {Path.joinpath(build_sub_dir, f"{unit.build_id}.{Podman.SCRIP_EX.value}")}'
            dest = f'-t {name}'
            end = ' . ;'

            cmd = [Podman.BUILD_CMD.value, build_args, IMAGE, script, dest, end]
            sp1print([
                TextBlock(' '.join(_ for _ in cmd), fore=Fore.YELLOW, style=Style.BRIGHT)
            ])
            if not self.dry_run:
                run(' '.join(_ for _ in cmd))

        elif self.backend == 'apptainer':
            # copy script
            sp1print([
                TextBlock('SCRIPT: ', fore=Fore.YELLOW, style=Style.BRIGHT),
                TextBlock(
                    f"{Path.joinpath(unit.node.path, 'build_scripts', f'{self.distro}.{Apptainer.SCRIP_EX.value}')}",
                    fore=Fore.GREEN),
                TextBlock(f" -> ", fore=Fore.YELLOW, style=Style.BRIGHT),
                TextBlock(f"{Path.joinpath(build_sub_dir, f'{unit.build_id}.{Apptainer.SCRIP_EX.value}')}", fore=Fore.GREEN)
            ])
            if not self.dry_run:
                shutil.copy(Path.joinpath(unit.node.path, 'build_scripts', f'{self.distro}.{Apptainer.SCRIP_EX.value}'),
                            Path.joinpath(build_sub_dir, f'{unit.build_id}.{Apptainer.SCRIP_EX.value}'))

            # no prolog needed for apptainer build

            # build
            p1print([
                TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": BUILDING ...")
            ])
            build_args = ' '.join(
                x for x in unit.node.build_spec['build_args']) if 'build_args' in unit.node.build_spec else ''
            IMAGE = f'--build-arg IMAGE={source}'
            script = f'{Path.joinpath(build_sub_dir, f"{unit.build_id}.{Apptainer.SCRIP_EX.value}")}'
            dest = f'{name}'
            end = ';'

            cmd = [Apptainer.BUILD_CMD.value, build_args, IMAGE, script, dest, end]
            sp1print([
                TextBlock(' '.join(_ for _ in cmd), fore=Fore.YELLOW, style=Style.BRIGHT)
            ])

        else:
            raise BackendNotSupported(self.backend)

        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": IMAGE "),
            TextBlock(f"{name}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(f" BUILT")
        ])
        print()
