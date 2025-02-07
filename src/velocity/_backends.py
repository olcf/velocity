"""Velocity backends."""

from abc import abstractmethod
from os import getenv
from pathlib import Path
from re import Match as re_Match, match as re_match, sub as re_sub
from shutil import which as shutil_which
from subprocess import run as subprocess_run

from loguru import logger

from velocity._exceptions import (
    BackendNotAvailable,
    BackendNotSupported,
    LineOutsideOfSection,
    RepeatedSection,
    TemplateSyntaxError,
)
from velocity._config import config
from velocity._graph import Image
from velocity._tools import OurABCMeta, trace_function


@trace_function
def _substitute(text: str, variables: dict[str, str], regex: str) -> str:
    """Substitute a variables in a string by a regex."""

    def _replace(m: re_Match):
        try:
            return str(variables[m.group(1)])
        except KeyError:
            logger.warning("The variable '{}' is undefined. Setting value to ''.".format(m.group(1)))

    return re_sub(regex, _replace, text)


class Backend(metaclass=OurABCMeta):
    """Abstract class for velocity backend."""

    template_sections: list[str] = [
        "@from",
        "@pre",
        "@copy",
        "@run",
        "@env",
        "@label",
        "@entry",
        "@post",
    ]

    existing_builds_cache: dict = dict()

    name: str = "backend"
    executable: str = "true"

    @classmethod
    @trace_function
    def _get_sections(cls, template: list[str]) -> dict[str, list[str]]:
        """Retrieve the sections from a VTMP."""

        sections: dict[str, list[str]] = dict()
        past_sections: list[str] = list()
        current_section: str | None = None

        for line in template:
            # if a line contains a section header
            if line in cls.template_sections:
                # move the current section to past_sections
                if current_section is not None:
                    past_sections.append(current_section)

                # check for repeated section
                if line in past_sections:
                    raise RepeatedSection(f"You have more than one '{line}' section in your template!")
                else:
                    current_section = line
                    if current_section not in sections:
                        sections[current_section] = list()

            else:
                # handel content lines
                if current_section is None:
                    raise LineOutsideOfSection("You have a line outside of a section in your template!")
                else:
                    sections[current_section].append(line)

        # remove empty sections
        del_list: list[str] = list()
        for sec in sections:
            if len(sections[sec]) == 0:
                del_list.append(sec)
        for sec in del_list:
            del sections[sec]

        return sections

    @classmethod
    @trace_function
    def _filter_content(cls, image: Image, text: str) -> str:
        """Filter conditionals and white space from a template line."""

        # handle conditionals
        res: re_Match[str] = re_match(r".*(\?\?([\S ]*)\|>(.*)\?\?).*", text)
        if res is not None:
            if image.satisfies(res.group(2)):
                text = re_sub(r"(\?\?.*\?\?)", res.group(3).strip(), text)
            else:
                text = re_sub(r"(\?\?.*\?\?)", "", text)

        # remove comments, newlines, and superfluous white space
        text = re_sub(r">>>.*", "", text)
        text = re_sub(r"\n", "", text)
        text = re_sub(r"^\s+|\s+$", "", text)

        return text

    @classmethod
    @trace_function
    def _load_template(cls, image: Image, variables: dict[str, str]) -> list[str]:
        """Load a template and parse it."""

        template: list[str] = list()
        with open(
            Path(image.path).joinpath("templates", "{}.vtmp".format(image.template)),
            "r",
        ) as file:
            contents: list[str] = file.readlines()
            for line in contents:
                fcon: str = cls._filter_content(image, _substitute(line, variables, r"{{\s*(\S+)\s*}}"))
                if fcon != "":
                    template.append(fcon)
        return template

    def __init__(self) -> None:
        super().__init__()

        # load configuration
        self.load_configuration()

    def generate_script(self, image: Image, variables: dict[str, str]) -> list[str]:
        """Generate a build script."""

        logger.debug("Variables: {}".format(variables))
        template: list[str] = self._load_template(image, variables)
        sections: dict[str, list[str]] = self._get_sections(template)
        script: list[str] = list()

        # @from
        try:
            if len(sections["@from"]) != 1:
                raise TemplateSyntaxError(
                    "You can only have one source in the @from section!",
                )
            elif len(sections["@from"][0].split()) != 1:
                raise TemplateSyntaxError("Your source must be a single string!", sections["@from"][0])
            else:
                script.extend(self._from(sections["@from"]))
        except KeyError:
            raise TemplateSyntaxError("You must have an @from section in your template!")
        # arguments
        script.extend(self._arguments(sections))
        # @pre
        if "@pre" in sections:
            script.extend(self._literal_section(sections["@pre"]))
        # @copy
        if "@copy" in sections:
            script.extend(self._copy(sections["@copy"]))
        # @run
        if "@run" in sections:
            env_ext: list[str] = list()
            script.extend(self._run(sections["@run"], env_ext))
            if len(env_ext) > 0:
                if "@env" in sections:
                    sections["@env"].extend(env_ext)
                else:
                    sections["@env"] = env_ext
        # @env
        if "@env" in sections:
            script.extend(self._env(sections["@env"]))
        # @label
        if "@label" in sections:
            script.extend(self._label(sections["@label"]))
        # @entry
        if "@entry" in sections:
            if len(sections["@entry"]) != 1:
                raise TemplateSyntaxError("You can only have one entrypoint!")
            script.extend(self._entry(sections["@entry"]))
        # @post
        if "@post" in sections:
            script.extend(self._literal_section(sections["@post"]))

        return script

    def is_available(self) -> bool:
        """Check if the current system has the requested backend."""

        if shutil_which(self.executable) is None:
            return False
        return True

    @abstractmethod
    def _from(self, contents: list[str]) -> list[str]:
        """Handle the @from section."""

    @abstractmethod
    def _arguments(self, all_contents: dict[str, list[str]]) -> list[str]:
        """Handle arguments."""

    @abstractmethod
    def _copy(self, contents: list[str]) -> list[str]:
        """Handle the @copy section."""

    @abstractmethod
    def _run(self, contents: list[str], label_contents: list[str]) -> list[str]:
        """Handle the @run section. If any !enver directives are found, return a list for the @env section."""

    @abstractmethod
    def _env(self, contents: list[str]) -> list[str]:
        """Handle the @env section."""

    @abstractmethod
    def _label(self, contents: list[str]) -> list[str]:
        """Handle the @label section."""

    @abstractmethod
    def _entry(self, contents: list[str]) -> list[str]:
        """Handle the @entry section."""

    @classmethod
    def _literal_section(cls, contents: list[str]) -> list[str]:
        """Handle literal sections."""

        ret: list = [""]
        for ln in contents:
            ret.append(ln.lstrip("|"))
        return ret

    @abstractmethod
    def generate_build_cmd(self, src: str, dest: str, args: list[str] = None) -> list[str]:
        """Generate CLI command to build."""

    @abstractmethod
    def format_image_name(self, path: Path, tag: str) -> str:
        """Create a name for the image build."""

    @abstractmethod
    def clean_up_old_image(self, name: str) -> str:
        """Generate CLI command to clean up an old image."""

    @abstractmethod
    def build_exists(self, name: str) -> bool:
        """Check if an images has been built."""

    @abstractmethod
    def generate_final_image_cmd(self, src: str, dest: str) -> str:
        """Generate command to move the last image in the build to its final destination."""

    @abstractmethod
    def curate_variables(self, variables: dict[str, str | bool]) -> None:
        """Curate the template variables with edits and additions for a specific backend."""

    @abstractmethod
    def load_configuration(self) -> None:
        """Load environment configuration for a specific backend."""


class Apptainer(Backend):
    """Apptainer backend."""

    name = "apptainer"
    executable = "apptainer"

    def _from(self, contents: list[str]) -> list[str]:
        ret: list[str] = list()
        res = re_match(r"^((?P<bootstrap>[\w-]*)(://))?(?P<main>[^\s]+)$", contents[0])
        if res is None:
            raise TemplateSyntaxError("Unknown source format in @from!")
        else:
            res = res.groupdict()

        if res["bootstrap"] is not None:
            match res["bootstrap"]:
                case "localimage":
                    logger.debug("Template @from source identified as 'localimage'")
                    ret.append("Bootstrap: localimage")
                    ret.append("From: {}".format(res["main"]))
                case "docker":
                    logger.debug("Template @from source identified as 'docker'")
                    ret.append("Bootstrap: docker")
                    ret.append("From: {}".format(res["main"]))
                case "oras":
                    logger.debug("Template @from source identified as 'oras'")
                    ret.append("Bootstrap: oras")
                    ret.append("From: {}".format(res["main"]))
                case _:
                    raise TemplateSyntaxError("Unknown bootstrap type '{}' in @from!".format(res["bootstrap"]))
        else:  # if the bootstrap type was not specified
            if re_match(r"^.*\.sif$", res["main"]):
                logger.debug("Template @from source identified as 'localimage'")
                ret.append("Bootstrap: localimage")
                ret.append("From: {}".format(res["main"]))
            elif re_match(r"^[^:\s]+(:[^\s]+)?$", contents[0]):
                logger.debug("Template @from source identified as 'docker'")
                ret.append("Bootstrap: docker")
                ret.append("From: {}".format(res["main"]))
            else:
                raise TemplateSyntaxError("Unknown source format in @from!")

        return ret

    def _arguments(self, all_contents: dict[str, list[str]]) -> list[str]:
        for si in all_contents.keys():
            for li in range(len(all_contents[si])):
                res = re_match(r".*(@@\s*(\S+)\s*@@).*", all_contents[si][li])
                if res is not None:
                    if len(res.group(2).split()) != 1:
                        raise TemplateSyntaxError("Arguments cannot have spaces in their names!")
                    else:
                        all_contents[si][li] = _substitute(
                            all_contents[si][li],
                            {res.group(2): f"{{{{ {res.group(2)} }}}}"},
                            r"@@\s*(\S+)\s*@@",
                        )
        return list()

    def _copy(self, contents: list[str]) -> list[str]:
        ret: list[str] = ["", "%files"]
        for ln in contents:
            if len(ln.split()) != 2:
                raise TemplateSyntaxError("Your '@copy' can only have one source and destination!", ln)
            ret.append("{}".format(ln))
        return ret

    def _run(self, contents: list[str], label_contents: list[str]) -> list[str]:
        ret: list[str] = ["", "%post"]
        for cmd in contents:
            # handel !envar directives
            if re_match(r"^!envar\s+.*", cmd):
                res = re_match(r"^!envar\s+(?P<name>\S+)\s+(?P<value>.*)$", cmd)
                cmd = 'export {name}="{value}"'.format(**res.groupdict())
                label_contents.append("{name} {value}".format(**res.groupdict()))
            ret.append("{}".format(cmd))
        return ret

    def _env(self, contents: list[str]) -> list[str]:
        ret: list[str] = ["", "%environment"]
        for env in contents:
            parts = env.split()
            ret.append('export {}="{}"'.format(parts[0], env.lstrip(parts[0]).strip(" ")))
        return ret

    def _label(self, contents: list[str]) -> list[str]:
        ret: list[str] = ["", "%labels"]
        for label in contents:
            parts = label.split()
            ret.append("{} {}".format(parts[0], label.lstrip(parts[0]).strip(" ")))
        return ret

    def _entry(self, contents: list[str]) -> list[str]:
        return ["", "%runscript", "{}".format(contents[0])]

    def generate_build_cmd(self, src: str, dest: str, args: list = None) -> list[str]:
        cmd: list[str] = ["{} build".format(self.executable)]
        # arguments
        if args is not None and len(args) > 0:
            cmd.append(" ".join(_ for _ in args) if args is not None else "")
        # destination
        cmd.append("{}".format(dest))
        # script
        cmd.append("{}".format(src))
        return [" ".join(_ for _ in cmd) + ";"]

    def format_image_name(self, path: Path, tag: str) -> str:
        return "{}{}".format(Path.joinpath(path, tag), ".sif" if ".sif" not in tag else "")

    def clean_up_old_image(self, name: str) -> str:
        return "/usr/bin/env true"

    def build_exists(self, name: str) -> bool:
        if name not in self.existing_builds_cache:
            if Path(name).is_file():
                self.existing_builds_cache[name] = True
            else:
                self.existing_builds_cache[name] = False
        return self.existing_builds_cache[name]

    def generate_final_image_cmd(self, src: str, dest: str) -> str:
        return "cp {} {}".format(src, dest)

    def curate_variables(self, variables: dict[str, str | bool]) -> None:
        pass

    def load_configuration(self) -> None:
        pass


class Docker(Backend):
    """Docker backend."""

    name = "docker"
    executable = "docker"

    def _from(self, contents: list[str]) -> list[str]:
        return [f"FROM {contents[0]}"]

    def _arguments(self, all_contents: dict[str, list[str]]) -> list[str]:
        ret: list[str] = list()
        for si in all_contents.keys():
            for li in range(len(all_contents[si])):
                res: re_Match[str] = re_match(r".*(@@\s*(\S+)\s*@@).*", all_contents[si][li])
                if res is not None:
                    if len(res.group(2).split()) != 1:
                        raise TemplateSyntaxError("Arguments cannot have spaces in their names!")
                    else:
                        ret.append("ARG {}".format(res.group(2)))
                        all_contents[si][li] = _substitute(
                            all_contents[si][li],
                            {res.group(2): "${}".format(res.group(2))},
                            r"@@\s*(\S+)\s*@@",
                        )
        if len(ret) > 0:
            ret.insert(0, "")
        return ret

    def _copy(self, contents: list[str]) -> list[str]:
        ret: list[str] = [""]
        for ln in contents:
            if len(ln.split()) != 2:
                raise TemplateSyntaxError("Entries in @copy can only have one source and destination!", ln)
            ret.append(f"COPY {ln}")
        return ret

    def _run(self, contents: list[str], label_contents: list[str]) -> list[str]:
        ret: list[str] = [""]
        for cmd in contents:
            # process !envar directives
            alt_cmd = cmd
            if re_match(r"^!envar\s+.*", cmd):
                res = re_match(r"^!envar\s+(?P<name>\S+)\s+(?P<value>.*)$", cmd)
                alt_cmd = 'export {name}="{value}"'.format(**res.groupdict())
                label_contents.append("{name} {value}".format(**res.groupdict()))
            # generate line
            ln = ""
            # place RUN on the first line
            if cmd == contents[0]:
                ln += "RUN "
            else:
                # indent following lines
                ln += "    "
            ln += alt_cmd
            # add '&& \\' to all but the last line
            if cmd != contents[-1] and cmd[-1] != "\\":  # ignore line that end in an escape
                ln += " && \\"
            ret.append(ln)
        return ret

    def _env(self, contents: list[str]) -> list[str]:
        ret: list[str] = [""]
        for env in contents:
            parts = env.split()
            # generate line
            ln = ""
            # add ENV to the first line
            if env == contents[0]:
                ln += "ENV "
            else:
                # indent following lines
                ln += "    "
            ln += f'{parts[0]}="{env.lstrip(parts[0]).strip(" ")}"'
            # add '\\' to all but the last line
            if env != contents[-1]:
                ln += " \\"
            ret.append(ln)
        return ret

    def _label(self, contents: list[str]) -> list[str]:
        ret: list[str] = [""]
        for label in contents:
            parts = label.split()
            if len(parts) != 2:
                raise TemplateSyntaxError("Label '{}' must have two parts!".format(label))
            # generate line
            ln = ""
            # add LABEL to the first line
            if label == contents[0]:
                ln += "LABEL "
            else:
                # indent following lines
                ln += "    "
            ln += f'{parts[0]}="{label.lstrip(parts[0]).strip(" ")}"'
            # add '\\' to all but the last line
            if label != contents[-1]:
                ln += " \\"
            ret.append(ln)
        return ret

    def _entry(self, contents: list[str]) -> list[str]:
        return ["", "ENTRYPOINT {}".format(contents[0].split())]

    def generate_build_cmd(self, src: str, dest: str, args: list = None) -> list[str]:
        cmd: list[str] = ["{} build".format(self.executable)]
        # arguments
        if args is not None and len(args) > 0:
            cmd.append(" ".join(_ for _ in args) if args is not None else "")
        # script
        cmd.append("-f {}".format(src))
        # destination
        cmd.append("-t {}".format(dest))
        # build dir
        cmd.append(".")
        return [" ".join(_ for _ in cmd) + ";"]

    def format_image_name(self, path: Path, tag: str) -> str:
        return "{}{}{}".format("localhost/" if "/" not in tag else "", tag, ":latest" if ":" not in tag else "")

    def clean_up_old_image(self, name: str) -> str:
        return "{} rmi {}".format(self.executable, name)

    def build_exists(self, name: str) -> bool:
        if name not in self.existing_builds_cache:
            res = subprocess_run(
                f"{self.executable} image ls -n" + " | awk '{print $1\":\"$2}'" + f" | grep {name}",
                shell=True,
                capture_output=True,
            )
            if res.returncode == 0:
                self.existing_builds_cache[name] = True
            else:
                self.existing_builds_cache[name] = False
        return self.existing_builds_cache[name]

    def generate_final_image_cmd(self, src: str, dest: str) -> str:
        return "{} tag {} {}".format(self.executable, src, dest)

    def curate_variables(self, variables: dict[str, str | bool]) -> None:
        pass

    def load_configuration(self) -> None:
        pass


class OpenShift(Docker):
    """Openshift-CI backend. Inherit from Docker because openshift uses docker as the container runtime."""

    name = "openshift"
    executable = "oc"

    def generate_build_cmd(self, src: str, dest: str, args: list = None) -> list[str]:
        build_name = dest[: dest.find(":")]
        arguments = (" " + " ".join(_ for _ in args)) if args is not None and len(args) > 0 else ""
        cmd: list[str] = [
            "cp {} {};".format(src, re_sub(r"(script$)", "Dockerfile", src)),  # copy script to Dockerfile
            "if ! {} get buildconfigs {}; then".format(
                self.executable, build_name
            ),  # create new build config if none exist
            "    {} new-build {} --name={} --to={} --allow-missing-imagestream-tags=true;".format(
                self.executable, re_sub(r"(/script$)", "", src), build_name, dest
            ),
            "fi;",
            '{} patch buildconfig/{} --patch \'{{"spec":{{"resources":{{"limits":{{"cpu":"{}","memory":"{}"}}}}}}}}\';'.format(
                self.executable, build_name, config.get("openshift:cpu:limit"), config.get("openshift:memory:limit")
            ),
            "{} start-build {} --from-dir={}{};".format(  # run build
                self.executable, build_name, re_sub(r"(/script$)", "", src), arguments
            ),
            "while : ; do",  # wait for image to be pushed
            "    status=$({} describe build {} 2>/dev/null | awk '$1 == \"Status:\" {{print $2}}');".format(
                self.executable, build_name
            ),
            '    if echo "$status" | grep -iP "complete" > /dev/null; then',
            '        echo "Build complete."; exit 0;',
            '    elif echo "$status" | grep -iP "new|pending|running" > /dev/null; then',
            '        echo "Waiting for build to complete ($(date)) ..."; sleep 30;',
            "    else",
            "        echo \"Build failed with state '${status}'!\" >&2; exit 1;",
            "    fi;",
            "done;",
        ]
        return cmd

    def format_image_name(self, path: Path, tag: str) -> str:
        if ":" in tag:  # if the name already has a tag assume this is the name provided by the user and do not change
            return tag
        return "v-" + tag + ":latest"  # append a "v-" to avoid failures due to the name starting with a number

    def clean_up_old_image(self, name: str) -> str:
        return "{} delete buildconfigs {}; {} delete imagestream {};".format(
            self.executable, name[: name.find(":")], self.executable, name[: name.find(":")]
        )

    def build_exists(self, name: str) -> bool:
        if name not in self.existing_builds_cache:
            res = subprocess_run("{} get imagetags {};".format(self.executable, name), shell=True, capture_output=True)
            if res.returncode == 0:
                self.existing_builds_cache[name] = True
            else:
                self.existing_builds_cache[name] = False
        return self.existing_builds_cache[name]

    def generate_final_image_cmd(self, src: str, dest: str) -> str:
        return "{} tag {} {};".format(self.executable, src, dest)

    def curate_variables(self, variables: dict[str, str | bool]) -> None:
        # add openshift variables
        variables["__openshift_cpu_limit__"] = config.get("openshift:cpu:limit")
        variables["__openshift_memory_limit__"] = config.get("openshift:memory:limit")

        # update "__threads__" to match "openshift:cpu:limit"
        openshift_nproc = int(int(re_sub(r"[^0-9]", "", config.get("openshift:cpu:limit"))) / 1000)
        variables["__threads__"] = str(min(int(variables["__threads__"]), max(1, openshift_nproc)))

    def load_configuration(self) -> None:
        # cpu limit
        cpu_limit = getenv("VELOCITY_OPENSHIFT_CPU_LIMIT")
        if cpu_limit is not None:
            config.set("openshift:cpu:limit", cpu_limit)
        elif config.get("openshift:cpu:limit") is None:
            config.set("openshift:cpu:limit", "1000m")
        # memory limit
        memory_limit = getenv("VELOCITY_OPENSHIFT_MEMORY_LIMIT")
        if memory_limit is not None:
            config.set("openshift:memory:limit", memory_limit)
        elif config.get("openshift:memory:limit") is None:
            config.set("openshift:memory:limit", "2Gi")


class Podman(Docker):
    """Podman backend. Inherit from Docker because for our purposes they are the same."""

    name = "podman"
    executable = "podman"


class Singularity(Apptainer):
    """Singularity backend. Inherit from Apptainer because that is what Singularity really is."""

    name = "singularity"
    executable = "singularity"


@trace_function
def get_backend() -> Backend:
    backend = config.get("velocity:backend").lower()
    if backend == "apptainer":
        b = Apptainer()
    elif backend == "docker":
        b = Docker()
    elif backend == "openshift":
        b = OpenShift()
    elif backend == "podman":
        b = Podman()
    elif backend == "singularity":
        b = Singularity()
    else:
        raise BackendNotSupported(backend)

    # check that backend is available
    if b.is_available():
        return b
    else:
        raise BackendNotAvailable("Your system does not have the '{}' backend".format(b.name))
