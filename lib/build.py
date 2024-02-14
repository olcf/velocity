import random
import shutil
import os
import subprocess
import string
import yaml
from lib.graph import Node
from lib.print import h1print, p1print, sp1print


class BuildUnit:

    def __init__(self, node: Node):
        self.node = node
        self.build_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        self.build_args = set()
        self.files = set()
        self.prolog = None

        # load build settings
        if os.path.isfile(f'{self.node.path}/{self.node.system}/spec.yaml'):
            with open(f'{self.node.path}/{self.node.system}/spec.yaml', 'r') as file:
                spec = yaml.safe_load(file)
                if 'build_args' in spec:
                    self.build_args = spec['build_args']
                if 'prolog' in spec:
                    self.prolog = spec['prolog']
                if 'files' in spec:
                    for f in spec['files']:
                        self.files.add((f'{self.node.path}/{self.node.system}/{f}', f))

        # add dockerfile
        self.files.add((f'{self.node.path}/{self.node.distro}.Dockerfile', f'{self.node.distro}.Dockerfile'))

    def get_build_command(self, source='', tag=''):
        build_args = ' '.join(_ for _ in self.build_args).strip(' ')
        IMAGE = f' --build-arg IMAGE={source}' if source != '' else ''
        docker_file = f'{self.build_id}.{self.node.distro}.Dockerfile'
        tag = tag if tag != '' else f'localhost/{self.build_id}:latest'

        return f'podman build {build_args}{IMAGE} -f {docker_file} -t {tag} .;'


class Builder:

    def __init__(self, build_seq, name=False, dry_run=False, build_dir='tmp/', clean_up=True):
        self.build_units = list()
        self.name = name
        self.dry_run = dry_run
        self.build_dir = build_dir
        self.clean_up = clean_up

        for node in build_seq:
            n = BuildUnit(node)
            self.build_units.append(n)

    def build(self):
        last = None
        for u in self.build_units:
            if u == self.build_units[-1] and self.name is not None:
                name = self.name
            else:
                name = f'localhost/{u.build_id}:latest'
            if last is None:
                build_image(u, '', name, self.dry_run, self.build_dir)
                if self.clean_up:
                    subprocess.run(f'podman untag {last}', shell=True)
                last = name
            else:
                build_image(u, last, name, self.dry_run, self.build_dir)
                if self.clean_up:
                    subprocess.run(f'podman untag {last}', shell=True)
                last = name

        if os.path.isdir(self.build_dir):
            os.rmdir(self.build_dir)


def build_image(unit: BuildUnit, source: str, name: str, dry_run: bool, build_dir):
    p1print(f"{unit.build_id}: START BUILD {unit.node.name}@={unit.node.tag}{' --DRY-RUN' if dry_run else ''} ...")

    if not os.path.isdir(build_dir) and not dry_run:
        os.mkdir(build_dir)

    p1print(f"{unit.build_id}: COPY FILES ...")
    for file in list(unit.files):
        sp1print(f"{file[0]} -> {build_dir}{unit.build_id}.{file[1]}")
        if not dry_run:
            shutil.copy(file[0], f'{build_dir}{unit.build_id}.{file[1]}')

    # save current dir and go to build dir
    pwd = os.getcwd()
    if not dry_run:
        os.chdir(build_dir)

    if unit.prolog:
        p1print(f"{unit.build_id}: PROLOG ...")
        if not dry_run:
            subprocess.run(f'{unit.build_id}.{unit.prolog}')

    p1print(f"{unit.build_id}: BUILDING ...")
    sp1print(unit.get_build_command(source, name))
    if not dry_run:
        os.system(unit.get_build_command(source, name))

    # return to previous dir
    os.chdir(pwd)

    p1print(f"{unit.build_id}: IMAGE {name} BUILT")
