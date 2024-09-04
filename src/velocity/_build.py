import datetime
import random
import re
import shutil
import os
import string
from timeit import default_timer as timer
from subprocess import Popen, PIPE
from queue import SimpleQueue
from threading import Thread
from pathlib import Path
from colorama import Fore, Style

from ._config import config
from ._graph import Image
from ._print import p1print, sp1print, TextBlock
from ._backends import get_backend


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


def run(cmd: str, log_file: Path = None, verbose: bool = False) -> None:
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

"""
class BuildUnit:

    def __init__(self, node: Image):
        self.node = node
        self.build_id = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
"""

class Builder:

    def __init__(self, bt: tuple[Image], build_name: str = None, dry_run: bool = False,
                 leave_tags: bool = True, verbose: bool = False):
        self.build_units = list()
        self.build_name = build_name
        self.dry_run = dry_run
        self.leave_tags = leave_tags
        self.verbose = verbose

        self.backend_engine = get_backend({})

        # create build_dir if it does not exist
        self.build_dir = Path(config.get("velocity:build_dir"))
        self.build_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        self.build_units = bt

    def build(self):
        # store pwd
        pwd = Path(Path().absolute())


        """# clear build_dir
        for entry in self.build_dir.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        """

        last = None  # last image that was built
        for u in self.build_units:

            if u == self.build_units[-1]:
                sorted_specs = [(bu.name, bu.version) for bu in self.build_units]
                sorted_specs.sort()
                tag = str(self.build_name if self.build_name is not None else
                          f"{'_'.join(f'{bu[0]}-{bu[1]}' for bu in sorted_specs)}__{config.get('velocity:system')}-{config.get('velocity:distro')}")
                name = self.backend_engine.format_image_name(Path(pwd.absolute()), tag)
            else:
                name = self.backend_engine.format_image_name(Path.joinpath(self.build_dir, u.id), u.id)

            self._build_image(u, last, name)
            if not self.dry_run and not self.leave_tags and last is not None:
                run(self.backend_engine.clean_up_old_image_cmd(last))
            last = name

        # go back to the starting dir
        os.chdir(pwd)

    def _build_image(self, unit: Image, src_image: str, name: str):
        # print start of build
        p1print([
            TextBlock(f"{unit.id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": BUILD "),
            TextBlock(f"{unit.name}@{unit.version}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(f"{' --DRY-RUN' if self.dry_run else ''} ...")
        ])

        start = timer()

        # create build dir and go to it
        build_sub_dir = Path.joinpath(self.build_dir, unit.id)
        build_sub_dir.mkdir(mode=0o744, exist_ok=True)
        os.chdir(build_sub_dir)

        # copy additional files
        if len(unit.files) > 0 and Path.joinpath(unit.path, "files").is_dir():
            p1print([
                TextBlock(f"{unit.id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": COPYING FILES ...")
            ])

            for entry in unit.files:
                # print copy operation
                if self.verbose:
                    sp1print([
                        TextBlock('DIR: ' if Path.joinpath(unit.path, "files", entry).is_dir() else 'FILE: ', fore=Fore.YELLOW, style=Style.BRIGHT),
                        TextBlock(f"{Path.joinpath(unit.path, 'files', entry).absolute()}", fore=Fore.GREEN),
                        TextBlock(f" -> ", fore=Fore.YELLOW, style=Style.BRIGHT),
                        TextBlock(f"{Path.joinpath(build_sub_dir, entry).absolute()}", fore=Fore.GREEN)
                    ])
                if Path.joinpath(unit.path, "files", entry).is_dir():
                    shutil.copytree(Path.joinpath(unit.path, "files", entry), Path.joinpath(build_sub_dir, entry))
                else:
                    shutil.copy(Path.joinpath(unit.path, "files", entry), Path.joinpath(build_sub_dir, entry))

        # parse template and create script...
        p1print([
            TextBlock(f"{unit.id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": GENERATING SCRIPT ...")
        ])
        if self.verbose:
            sp1print([
                TextBlock('SCRIPT: ', fore=Fore.YELLOW, style=Style.BRIGHT),
                TextBlock(f"{Path.joinpath(build_sub_dir, 'script')}", fore=Fore.GREEN)
            ])

        # get and update script variables
        script_variables = unit.variables.copy()
        script_variables.update({'__name__': unit.name})
        script_variables.update({'__version__': str(unit.version)})
        script_variables.update({'__timestamp__': str(datetime.datetime.now())})
        script_variables.update({'__threads__': str(int(os.cpu_count() * 0.75) if int(os.cpu_count() * 0.75) < 16 else 16)})
        if src_image is not None:
            script_variables.update({'__base__': src_image})

        script = self.backend_engine.generate_script(
            Path.joinpath(unit.path, 'templates', f'{unit.template}.vtmp'),
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
            unit.arguments
        )
        build_file_path = Path.joinpath(build_sub_dir, 'build')
        build_contents = ['#!/usr/bin/env bash']


        if unit.prolog is not None:
            p1print([
                TextBlock(f"{unit.id}", fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(f": RUNNING PROLOG ... && BUILDING ...")
            ])
            build_contents.append(unit.prolog.strip('\n'))
            build_contents.append(build_cmd)

        else:
            p1print([
                TextBlock(f"{unit.id}", fore=Fore.RED, style=Style.BRIGHT),
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

        end = timer()

        p1print([
            TextBlock(f"{unit.id}", fore=Fore.RED, style=Style.BRIGHT),
            TextBlock(f": IMAGE "),
            TextBlock(f"{name}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(' ('),
            TextBlock(f"{unit.name}@{unit.version}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(f") BUILT ["),
            TextBlock(f"{datetime.timedelta(seconds=round(end - start))}", fore=Fore.MAGENTA, style=Style.BRIGHT),
            TextBlock(']')
        ])
        print()  # new line
