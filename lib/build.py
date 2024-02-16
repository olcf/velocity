import random
import shutil
import os
import subprocess
import string
import yaml
from colorama import Fore, Back, Style
from lib.graph import Node
from lib.print import p1print, sp1print, TextBlock


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


class BuildUnit:

    def __init__(self, node: Node, path: str):
        self.node = node
        self.build_id = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
        self.build_args = set()
        self.prolog = None
        self.path = os.path.join(path, self.node.name, self.node.tag)
        self.additional_files = False

        # load build settings
        if os.path.isfile(f'{self.path}/{self.node.system}/spec.yaml'):
            self.additional_files = True
            with open(f'{self.path}/{self.node.system}/spec.yaml', 'r') as file:
                spec = yaml.safe_load(file)
                if 'build_args' in spec:
                    self.build_args = spec['build_args']
                if 'prolog' in spec:
                    self.prolog = spec['prolog']

    def get_build_command(self, build_dir, source='', tag=''):
        build_args = ' '.join(_ for _ in self.build_args).strip(' ')
        IMAGE = f' --build-arg IMAGE={source}' if source != '' else ''
        docker_file = os.path.join(build_dir, f'{self.node.distro}.Dockerfile')
        tag = tag if tag != '' else f'localhost/{self.build_id}:latest'

        return f'podman build {build_args}{IMAGE} -f {docker_file} -t {tag} .;'


class Builder:

    def __init__(self, bt: tuple[Node], image_dir: str, build_name=None, dry_run=False,
                 build_dir=os.path.join(os.getcwd(), 'tmp'), clean_up=True):
        self.build_units = list()
        self.build_name = build_name
        self.dry_run = dry_run
        self.build_dir = build_dir
        self.clean_up = clean_up

        for node in bt:
            self.build_units.append(BuildUnit(node, image_dir))

    def build(self):
        last = None
        for u in self.build_units:
            if u == self.build_units[-1] and self.build_name is not None:
                name = self.build_name
            else:
                name = f'localhost/{u.build_id}:latest'
            if last is None:
                self._build_image(u, '', name)
                if self.clean_up and not self.dry_run and last is not None:
                    run(f'podman untag {last}')
                last = name
            else:
                self._build_image(u, last, name)
                if self.clean_up and not self.dry_run and last is not None:
                    run(f'podman untag {last}')
                last = name

    def _build_image(self, unit: BuildUnit, source: str, name: str):
        # print start of build
        text_blocks = [
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": BUILD "),
            TextBlock(f"{unit.node.name}@={unit.node.tag}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(f"{' --DRY-RUN' if self.dry_run else ''} ...")
        ]
        p1print(text_blocks)

        # create build dir
        if not os.path.isdir(self.build_dir) and not self.dry_run:
            os.makedirs(self.build_dir, exist_ok=True)

        text_blocks = [
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": COPYING FILES ...")
        ]
        p1print(text_blocks)
        # copy additional files
        if unit.additional_files:
            for entry in os.listdir(os.path.join(unit.path, unit.node.system)):
                # print copy operation
                sp1print([
                    TextBlock(f"{os.path.join(unit.path, unit.node.system, entry)}", fore=Fore.GREEN),
                    TextBlock(f" -> ", fore=Fore.YELLOW, style=Style.BRIGHT),
                    TextBlock(f"{os.path.join(self.build_dir, entry)}", fore=Fore.GREEN)
                ])
                if self.dry_run:
                    continue
                elif os.path.isdir(os.path.join(unit.path, unit.node.system, entry)):
                    shutil.copytree(os.path.join(unit.path, unit.node.system, entry),
                                    os.path.join(self.build_dir, entry))
                else:
                    shutil.copy(os.path.join(unit.path, unit.node.system, entry),
                                os.path.join(self.build_dir, entry))

        # copy dockerfile
        # print copy operation
        sp1print([
            TextBlock(f"{os.path.join(unit.path, f'{unit.node.system}.Dockerfile')}", fore=Fore.GREEN),
            TextBlock(f" -> ", fore=Fore.YELLOW, style=Style.BRIGHT),
            TextBlock(f"{os.path.join(self.build_dir, f'{unit.node.system}.Dockerfile')}", fore=Fore.GREEN)
        ])
        if not self.dry_run:
            shutil.copy(os.path.join(unit.path, f'{unit.node.distro}.Dockerfile'),
                        os.path.join(self.build_dir, f'{unit.node.distro}.Dockerfile'))

        # save current dir and go to build dir
        pwd = os.getcwd()
        if not self.dry_run:
            os.chdir(self.build_dir)

        if unit.prolog:
            text_blocks = [
                TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": RUN PROLOG ...")
            ]
            p1print(text_blocks)
            if not self.dry_run:
                os.chmod(os.path.join(self.build_dir, unit.prolog), 0o774)
                run(os.path.join(self.build_dir, unit.prolog))

        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": BUILDING ...")
        ])
        sp1print([
            TextBlock(unit.get_build_command(self.build_dir, source, name), fore=Fore.YELLOW, style=Style.BRIGHT)
        ])
        if not self.dry_run:
            run(unit.get_build_command(self.build_dir, source, name))

        # return to previous dir and delete build dir
        os.chdir(pwd)
        if os.path.isdir(self.build_dir):
            shutil.rmtree(self.build_dir)

        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": IMAGE "),
            TextBlock(f"{name}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(f" BUILT")
        ])
