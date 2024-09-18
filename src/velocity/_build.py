"""Build velocity images."""

import datetime
import shutil
import os
from timeit import default_timer as timer
from subprocess import Popen, PIPE
from queue import SimpleQueue
from threading import Thread
from pathlib import Path
from colorama import Fore, Style
from platform import processor as arch
from ._config import config
from ._graph import Image
from ._print import header_print, indent_print, TextBlock
from ._backends import get_backend, Backend


def read_pipe(pipe: PIPE, topic: SimpleQueue, prefix: str, log: SimpleQueue) -> None:
    """Read a subprocess PIPE and place lines on topic queue and log queue."""
    while True:
        ln = pipe.readline()
        if ln == "":
            break
        else:
            topic.put(ln.strip("\n"))
            log.put("{} {}".format(prefix, ln.strip("\n")))


def run(cmd: str, log_file: Path = None, verbose: bool = False) -> None:
    """Run a system command logging all output to a file and print if verbose."""
    # open log file (set to False if none is provided)
    file = open(log_file, "w") if log_file is not None else False

    log = SimpleQueue()
    stdout = SimpleQueue()
    stderr = SimpleQueue()

    process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    out = Thread(target=read_pipe, args=(process.stdout, stdout, "STDOUT:", log))
    err = Thread(target=read_pipe, args=(process.stderr, stderr, "STDERR:", log))

    out.start()
    err.start()

    # loop for real time output
    while process.poll() is None:
        if verbose and not stdout.empty():
            indent_print([TextBlock(stdout.get(), fore=Fore.GREEN, style=Style.DIM)])
        if file and not log.empty():
            file.write(log.get() + "\n")
            file.flush()  # TODO is this needed?

    out.join()
    err.join()

    # clear stdout & log
    if verbose:
        while not stdout.empty():
            indent_print([TextBlock(stdout.get(), fore=Fore.GREEN, style=Style.DIM)])

    if file:
        while not log.empty():
            file.write(log.get() + "\n")
            file.flush()  # TODO is this needed?
        file.close()

    # if an error was encountered exit with the subprocess exit code
    if process.poll() != 0:
        while stderr.qsize():
            indent_print([TextBlock(stderr.get(), fore=Fore.RED, style=Style.DIM)])
        exit(process.poll())


class ImageBuilder:
    """Image building class."""

    def __init__(
        self,
        bt: tuple[Image],
        build_name: str = None,
        dry_run: bool = False,
        remove_tags: bool = True,
        clean_build_dir: bool = False,
        verbose: bool = False,
    ) -> None:
        self.build_units: tuple[Image] = bt
        self.build_name: str = build_name
        self.dry_run: bool = dry_run
        self.remove_tags: bool = remove_tags
        self.clean_build_dir: bool = clean_build_dir
        self.verbose: bool = verbose

        self.backend_engine: Backend = get_backend()

        # create build_dir if it does not exist
        self.build_dir = Path(config.get("velocity:build_dir"))
        self.build_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        self.variables: dict[str, str] = dict()
        for i in self.build_units:
            self.variables["__{}__version__".format(i.name)] = i.version.__str__()
            self.variables["__{}__version_major__".format(i.name)] = i.version.major.__str__()
            self.variables["__{}__version_minor__".format(i.name)] = i.version.minor.__str__()
            self.variables["__{}__version_patch__".format(i.name)] = i.version.patch.__str__()
            self.variables["__{}__version_suffix__".format(i.name)] = i.version.suffix.__str__()

    def build(self) -> None:
        """Launch image builds."""
        # store pwd
        pwd = Path(Path().absolute())

        # clean build_dir
        if self.clean_build_dir:
            for entry in self.build_dir.iterdir():
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()

        last = str()  # last image that was built
        build_names: list[str] = list()
        for u in self.build_units:
            name = self.backend_engine.format_image_name(
                Path.joinpath(self.build_dir, "{}-{}-{}".format(u.name, u.version, u.id)), u.id
            )
            self._build_image(u, last, name)
            last = name
            build_names.append(name)

        tag = str(
            self.build_name
            if self.build_name is not None
            else "{}__{}-{}".format(
                "_".join(f"{bu.name}-{bu.version}" for bu in reversed(self.build_units)),
                config.get("velocity:system"),
                config.get("velocity:distro"),
            )
        )

        final_name = self.backend_engine.format_image_name(Path(pwd.absolute()), tag)
        if not self.dry_run:
            run(self.backend_engine.generate_final_image_cmd(last, final_name))
        header_print([TextBlock("BUILT: "), TextBlock(final_name, fore=Fore.MAGENTA, style=Style.BRIGHT)])

        if not self.dry_run and self.remove_tags:
            for bn in build_names:
                run(self.backend_engine.clean_up_old_image_tag(bn))

        # go back to the starting dir
        os.chdir(pwd)

    def _build_image(self, unit: Image, src_image: str, name: str):
        """Build an individual image."""
        # print start of build
        header_print(
            [
                TextBlock(unit.id, fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(": BUILD "),
                TextBlock("{}@{}".format(unit.name, unit.version), fore=Fore.MAGENTA, style=Style.BRIGHT),
                TextBlock("{} ...".format(" --DRY-RUN" if self.dry_run else "")),
            ]
        )

        start = timer()

        # create build dir and go to it
        build_sub_dir = Path.joinpath(self.build_dir, "{}-{}-{}".format(unit.name, unit.version, unit.id))
        build_sub_dir.mkdir(mode=0o744, exist_ok=True)
        os.chdir(build_sub_dir)

        # copy additional files
        if len(unit.files) > 0:
            header_print([TextBlock(unit.id, fore=Fore.RED, style=Style.BRIGHT), TextBlock(": COPYING FILES ...")])
            for entry in unit.files:
                # print copy operation
                if self.verbose:
                    indent_print(
                        [
                            TextBlock(
                                "DIR: " if Path.joinpath(unit.path, "files", entry).is_dir() else "FILE: ",
                                fore=Fore.YELLOW,
                                style=Style.BRIGHT,
                            ),
                            TextBlock(str(Path.joinpath(unit.path, "files", entry).absolute()), fore=Fore.GREEN),
                            TextBlock(" -> ", fore=Fore.YELLOW, style=Style.BRIGHT),
                            TextBlock(str(Path.joinpath(build_sub_dir, entry).absolute()), fore=Fore.GREEN),
                        ]
                    )
                if Path.joinpath(unit.path, "files", entry).is_dir():
                    shutil.copytree(Path.joinpath(unit.path, "files", entry), Path.joinpath(build_sub_dir, entry))
                else:
                    shutil.copy(Path.joinpath(unit.path, "files", entry), Path.joinpath(build_sub_dir, entry))

        # parse template and create script...
        header_print([TextBlock(unit.id, fore=Fore.RED, style=Style.BRIGHT), TextBlock(": GENERATING SCRIPT ...")])
        if self.verbose:
            indent_print(
                [
                    TextBlock("SCRIPT: ", fore=Fore.YELLOW, style=Style.BRIGHT),
                    TextBlock(str(Path.joinpath(build_sub_dir, "script")), fore=Fore.GREEN),
                ]
            )

        # get and update script variables
        script_variables = unit.variables.copy()
        script_variables.update({"__name__": unit.name})
        script_variables.update({"__version__": str(unit.version)})
        script_variables.update({"__version_major__": str(unit.version.major)})
        script_variables.update({"__version_minor__": str(unit.version.minor)})
        script_variables.update({"__version_patch__": str(unit.version.patch)})
        script_variables.update({"__version_suffix__": str(unit.version.suffix)})
        script_variables.update({"__timestamp__": str(datetime.datetime.now())})
        script_variables.update(
            {"__threads__": str(int(os.cpu_count() * 0.75) if int(os.cpu_count() * 0.75) < 16 else 16)}
        )
        script_variables.update({"__arch__": arch()})
        if src_image is not None:
            script_variables.update({"__base__": src_image})
        script_variables.update(self.variables)

        script = self.backend_engine.generate_script(unit, script_variables)
        # write out script
        with open(Path.joinpath(build_sub_dir, "script"), "w") as out_file:
            for line in script:
                if self.verbose:
                    indent_print([TextBlock(line, fore=Fore.BLUE, style=Style.DIM)])
                out_file.writelines(line + "\n")

        # run prolog & build
        build_cmd = self.backend_engine.generate_build_cmd(
            str(Path.joinpath(build_sub_dir, "script")), name, unit.arguments
        )
        build_file_path = Path.joinpath(build_sub_dir, "build")
        build_contents = ["#!/usr/bin/env bash"]

        if unit.prolog is not None:
            header_print(
                [
                    TextBlock(unit.id, fore=Fore.RED, style=Style.BRIGHT),
                    TextBlock(": RUNNING PROLOG ... && BUILDING ..."),
                ]
            )
            build_contents.append(unit.prolog.strip("\n"))
            build_contents.append(build_cmd)

        else:
            header_print([TextBlock(unit.id, fore=Fore.RED, style=Style.BRIGHT), TextBlock(": BUILDING ...")])
            build_contents.append(build_cmd)

        with open(build_file_path, "w") as build_file:
            for line in build_contents:
                build_file.write(line + "\n")
                if self.verbose:
                    indent_print([TextBlock(line, fore=Fore.YELLOW, style=Style.BRIGHT)])

        build_file_path.chmod(0o744)

        if not self.dry_run:
            if self.backend_engine.build_exists(name):
                if self.verbose:
                    indent_print(
                        [TextBlock("Using cached image {} ...".format(name), fore=Fore.GREEN, style=Style.DIM)]
                    )
            else:
                run(str(build_file_path.absolute()), log_file=Path.joinpath(build_sub_dir, "log"), verbose=self.verbose)

        end = timer()

        header_print(
            [
                TextBlock(unit.id, fore=Fore.RED, style=Style.BRIGHT),
                TextBlock(": IMAGE "),
                TextBlock(name, fore=Fore.MAGENTA, style=Style.BRIGHT),
                TextBlock(" ("),
                TextBlock("{}@{}".format(unit.name, unit.version), fore=Fore.MAGENTA, style=Style.BRIGHT),
                TextBlock(") BUILT ["),
                TextBlock(str(datetime.timedelta(seconds=round(end - start))), fore=Fore.MAGENTA, style=Style.BRIGHT),
                TextBlock("]"),
            ]
        )
        print()  # new line
