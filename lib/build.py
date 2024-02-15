import random
import shutil
import os
import subprocess
import string
import yaml
from lib.graph import Node
from lib.print import h1print, p1print, sp1print


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
                if self.clean_up and not self.dry_run:
                    subprocess.run(f'podman untag {last}', shell=True)
                last = name
            else:
                self._build_image(u, last, name)
                if self.clean_up and not self.dry_run:
                    subprocess.run(f'podman untag {last}', shell=True)
                last = name

    def _build_image(self, unit: BuildUnit, source: str, name: str):
        p1print(
            f"{unit.build_id}: BUILD {unit.node.name}@={unit.node.tag}{' --DRY-RUN' if self.dry_run else ''} ...")

        # create build dir
        if not os.path.isdir(self.build_dir) and not self.dry_run:
            os.makedirs(self.build_dir, exist_ok=True)

        p1print(f"{unit.build_id}: COPYING FILES ...")
        # copy additional files
        if unit.additional_files:
            for entry in os.listdir(os.path.join(unit.path, unit.node.system)):
                sp1print(f'{os.path.join(unit.path, unit.node.system, entry)} -> {os.path.join(self.build_dir, entry)}')
                if self.dry_run:
                    continue
                elif os.path.isdir(os.path.join(unit.path, unit.node.system, entry)):
                    shutil.copytree(os.path.join(unit.path, unit.node.system, entry),
                                    os.path.join(self.build_dir, entry))
                else:
                    shutil.copy(os.path.join(unit.path, unit.node.system, entry),
                                os.path.join(self.build_dir, entry))
        sp1print(f"{os.path.join(unit.path, f'{unit.node.system}.Dockerfile')} -> "
                 f"{os.path.join(self.build_dir, f'{unit.node.system}.Dockerfile')}")
        # copy dockerfile
        if not self.dry_run:
            shutil.copy(os.path.join(unit.path, f'{unit.node.distro}.Dockerfile'),
                        os.path.join(self.build_dir, f'{unit.node.distro}.Dockerfile'))

        # save current dir and go to build dir
        pwd = os.getcwd()
        if not self.dry_run:
            os.chdir(self.build_dir)

        if unit.prolog:
            p1print(f"{unit.build_id}: RUN PROLOG ...")
            if not self.dry_run:
                os.chmod(os.path.join(self.build_dir, unit.prolog), 0o774)
                subprocess.run(os.path.join(self.build_dir, unit.prolog), shell=True)

        p1print(f"{unit.build_id}: BUILDING ...")
        sp1print(unit.get_build_command(self.build_dir, source, name))
        if not self.dry_run:
            process = subprocess.Popen(unit.get_build_command(self.build_dir, source, name),
                                       shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                elif output != '':
                    sp1print(output.strip('\n'))
            if process.poll() != 0:
                exit(process.poll())

        # return to previous dir and delete build dir
        os.chdir(pwd)
        if os.path.isdir(self.build_dir):
            shutil.rmtree(self.build_dir)

        p1print(f"{unit.build_id}: IMAGE {name} BUILT")
