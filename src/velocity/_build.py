"""Build velocity images."""

from datetime import datetime, timedelta
from os import chdir, cpu_count
from pathlib import Path
from platform import processor as arch
from shutil import copy as shutil_copy, copytree, rmtree
from threading import Thread
from timeit import default_timer as timer
from queue import SimpleQueue
from subprocess import PIPE, Popen

from colorama import Fore, Style
from loguru import logger

from velocity._config import config
from velocity._graph import Image
from velocity._print import TextBlock, header_print, indent_print
from velocity._backends import Backend, get_backend
from velocity._tools import OurMeta, trace_function


@trace_function
def read_pipe(pipe: PIPE, topic: SimpleQueue, prefix: str, log: SimpleQueue) -> None:
    """Read a subprocess PIPE and place lines on topic queue and log queue."""
    while True:
        ln = pipe.readline()
        if ln == "":
            break
        else:
            topic.put(ln.strip("\n"))
            log.put("{} {}".format(prefix, ln.strip("\n")))


@trace_function
def run(cmd: str, log_file: Path = None, verbose: bool = False) -> None:
    """Run a system command logging all output to a file and print if verbose."""
    # open log file (set to False if none is provided)
    logger.debug("Running command: {}".format(cmd))
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


class ImageBuilder(metaclass=OurMeta):
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

        self.variables: dict[str, str] = {
            "__backend__": self.backend_engine.name,
            "__backend_executable__": self.backend_engine.executable,
            "__threads__": str(int(cpu_count() * 0.75) if int(cpu_count() * 0.75) < 16 else 16),
            "__arch__": arch(),
            "__timestamp__": str(datetime.now()),
        }
        for u in self.build_units:
            self.variables["__{}__version__".format(u.name)] = str(u.version)
            self.variables["__{}__version_major__".format(u.name)] = str(u.version.major)
            self.variables["__{}__version_minor__".format(u.name)] = str(u.version.minor)
            self.variables["__{}__version_patch__".format(u.name)] = str(u.version.patch)
            self.variables["__{}__version_suffix__".format(u.name)] = str(u.version.suffix)

    def build(self) -> None:
        """Launch image builds."""
        # store pwd
        pwd = Path(Path().absolute())

        # clean build_dir
        if self.clean_build_dir:
            for entry in self.build_dir.iterdir():
                if entry.is_dir():
                    rmtree(entry)
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
            else "{}_{}-{}".format(
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
        chdir(pwd)

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
        chdir(build_sub_dir)

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
                    copytree(Path.joinpath(unit.path, "files", entry), Path.joinpath(build_sub_dir, entry))
                else:
                    shutil_copy(Path.joinpath(unit.path, "files", entry), Path.joinpath(build_sub_dir, entry))

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
        script_variables = {
            "__image_id__": unit.id,
            "__name__": unit.name,
            "__version__": str(unit.version),
            "__version_major__": str(unit.version.major),
            "__version_minor__": str(unit.version.minor),
            "__version_patch__": str(unit.version.patch),
            "__version_suffix__": str(unit.version.suffix),
        }
        if src_image is not None:
            script_variables.update({"__base__": src_image})
        script_variables.update(self.variables)
        script_variables.update(unit.variables)

        script = self.backend_engine.generate_script(unit, script_variables)
        # write out script
        with open(Path.joinpath(build_sub_dir, "script"), "w") as out_file:
            for line in script:
                if self.verbose:
                    indent_print([TextBlock(line, fore=Fore.BLUE, style=Style.DIM)])
                out_file.writelines(line + "\n")

        # write out variables
        variables_file = build_sub_dir.joinpath("variables")
        with open(variables_file, "w") as fo:
            for k, v in script_variables.items():
                if v == "None":
                    fo.write("export {}=''".format(k) + "\n")
                else:
                    fo.write("export {}={}".format(k, v) + "\n")

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
            build_contents.extend(["### VARIABLES ###", f"source {variables_file.absolute()}"])
            build_contents.append("### PROLOG ###")
            build_contents.extend(unit.prolog.strip("\n").split("\n"))
        else:
            header_print([TextBlock(unit.id, fore=Fore.RED, style=Style.BRIGHT), TextBlock(": BUILDING ...")])

        build_contents.append("### BUILD ###")
        build_contents.extend(build_cmd)

        with open(build_file_path, "w") as build_file:
            for line in build_contents:
                build_file.write(line + "\n")
                if self.verbose and not self.backend_engine.build_exists(name):
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
                TextBlock(str(timedelta(seconds=round(end - start))), fore=Fore.MAGENTA, style=Style.BRIGHT),
                TextBlock("]"),
            ]
        )
        print()  # new line
