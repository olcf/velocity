import datetime
import random
import re
import shutil
import os
import string
from subprocess import Popen, PIPE
from queue import SimpleQueue
from threading import Thread
from pathlib import Path
from colorama import Fore, Style
from lib.graph import Node
from lib.print import p1print, sp1print, TextBlock
from lib.exceptions import BackendNotSupported
from lib.backends import get_backend


def read_pipe(pipe: PIPE, topic: SimpleQueue, prefix: str, log: SimpleQueue) -> None:
    """
        Read a subprocess PIPE and place lines on topic queue and log queue
    """
    while True:
        ln = pipe.readline()
        if ln == '':
            break
        else:
            topic.put(ln.strip('\n'))
            log.put("{} {}".format(prefix, ln.strip('\n')))


def run(cmd: str, log_file: Path = None, verbose: bool = False):
    """
        Run a system command logging all output and print if verbose.
    """

    # open log file (set to False if none is provided)
    file = open(log_file, 'w') if log_file is not None else False

    log = SimpleQueue()
    stdout = SimpleQueue()
    stderr = SimpleQueue()

    process = Popen(
        cmd,
        shell=True,
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True
    )

    out = Thread(target=read_pipe, args=(process.stdout, stdout, 'STDOUT:', log))
    err = Thread(target=read_pipe, args=(process.stderr, stderr, 'STDERR:', log))

    out.start()
    err.start()

    # loop for real time output
    while process.poll() is None:
        if not stdout.empty() and verbose:
            sp1print([
                TextBlock(stdout.get(), fore=Fore.GREEN, style=Style.DIM)
            ])
        if not log.empty() and file:
            file.write(log.get() + '\n')
            file.flush()

    out.join()
    err.join()

    # clear stdout & log
    if verbose:
        while not stdout.empty():
            sp1print([
                TextBlock(stdout.get(), fore=Fore.GREEN, style=Style.DIM)
            ])

    if file:
        while not log.empty():
            file.write(log.get() + '\n')
            file.flush()
        file.close()

    # if an error was encountered exit with the subprocess exit code
    if process.poll() != 0:
        while stderr.qsize():
            ln = stderr.get()
            if verbose:
                sp1print([
                    TextBlock(ln, fore=Fore.RED, style=Style.DIM)
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

        last = None  # last image that was built
        for u in self.build_units:
            if self.backend == 'podman':
                if u == self.build_units[-1]:  # if this is the last image
                    name = str(self.build_name if self.build_name is not None else
                               f'{u.node.name}__{u.node.tag}__{self.system}__{self.distro}')
                    if '/' not in name and ':' not in name:
                        name = f'localhost/{name}:latest'
                else:
                    name = f'localhost/{u.build_id}:latest'
            elif self.backend == 'apptainer':
                if u == self.build_units[-1]:  # if this is the last image
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
                if self.verbose:
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

        # parse template and create script...
        p1print([
            TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": GENERATING SCRIPT ...")
        ])
        if self.verbose:
            sp1print([
                TextBlock('SCRIPT: ', fore=Fore.YELLOW, style=Style.BRIGHT),
                TextBlock(f"{Path.joinpath(build_sub_dir, 'script')}", fore=Fore.GREEN)
            ])

        # get and update script variables
        script_variables = unit.node.build_specifications['variables'] \
            if 'variables' in unit.node.build_specifications else dict()
        script_variables.update({'__name__': unit.node.name})
        script_variables.update({'__tag__': unit.node.tag})
        script_variables.update({'__timestamp__': datetime.datetime.now()})
        if src_image is not None:
            script_variables.update({'__base__': src_image})

        script = self.backend_engine.generate_script(
            Path.joinpath(unit.node.path, 'templates', f'{self.distro}.vtmp'),
            script_variables
        )
        # write out script
        with open(Path.joinpath(build_sub_dir, 'script'), 'w') as out_file:
            for line in script:
                if self.verbose:
                    sp1print([
                        TextBlock(line, fore=Fore.BLUE, style=Style.DIM)
                    ])
                out_file.writelines(line + '\n')

        # run prolog & build
        build_cmd = self.backend_engine.generate_build_cmd(
            str(Path.joinpath(build_sub_dir, 'script')),
            name,
            unit.node.build_specifications['arguments'] if 'arguments' in unit.node.build_specifications else None
        )
        build_file_path = Path.joinpath(build_sub_dir, 'build')
        build_contents = ['#!/usr/bin/env bash']

        if 'prolog' in unit.node.build_specifications:
            p1print([
                TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": RUNNING PROLOG ... && BUILDING ...")
            ])
            with open(Path.joinpath(build_sub_dir, unit.node.build_specifications['prolog']), 'r') as prolog:
                for line in prolog:
                    striped = re.sub(r'#.*', '', line)
                    if not striped.isspace():
                        build_contents.append(striped.strip('\n'))
            build_contents.append(build_cmd)

        else:
            p1print([
                TextBlock(f"{unit.build_id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": BUILDING ...")
            ])
            build_contents.append(build_cmd)

        with open(build_file_path, 'w') as build_file:
            for line in build_contents:
                build_file.write(line + '\n')
                if self.verbose:
                    sp1print([
                        TextBlock(line, fore=Fore.YELLOW, style=Style.BRIGHT)
                    ])

        build_file_path.chmod(0o744)

        if not self.dry_run:
            run(str(build_file_path.absolute()), log_file=Path.joinpath(build_sub_dir, 'log'), verbose=self.verbose)

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
