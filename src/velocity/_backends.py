"""Velocity backends."""

from re import Match as re_Match, sub as re_sub, match as re_match
from loguru import logger
from shutil import which as shutil_which
from pathlib import Path
from abc import ABC, abstractmethod
from ._exceptions import (
    RepeatedSection,
    LineOutsideOfSection,
    TemplateSyntaxError,
    BackendNotSupported,
    BackendNotAvailable,
)
from ._config import config
from ._graph import Image


def _substitute(text: str, variables: dict[str, str], regex: str) -> str:
    """Substitute a variables in a string by a regex."""

    def _replace(m: re_Match):
        try:
            return str(variables[m.group(1)])
        except KeyError:
            logger.warning("The variable '{}' is undefined. Setting value to ''.".format(m.group(1)))

    return re_sub(regex, _replace, text)


class Backend(ABC):
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

    @classmethod
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

    def __init__(self, name: str, executable: str) -> None:
        self.name: str = name
        self.executable: str = executable

    def generate_script(self, image: Image, variables: dict[str, str]) -> list[str]:
        """Generate a build script e.g. .dockerfile/.def"""
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
    def generate_build_cmd(self, src: str, dest: str, args: list[str] = None) -> str:
        """Generate CLI command to build."""

    @abstractmethod
    def format_image_name(self, path: Path, tag: str) -> str:
        """Create a name for the image build."""

    @abstractmethod
    def clean_up_old_image_tag(self, name: str) -> str:
        """Generate CLI command to clean up an old image."""

    @abstractmethod
    def build_exists(self, name: str) -> bool:
        """Check if an images has been built."""

    @abstractmethod
    def generate_final_image_cmd(self, src: str, dest: str) -> str:
        """Generate command to move the last image in the build to its final destination."""


class Podman(Backend):
    """Podman backend."""

    def __init__(self):
        super().__init__(name="podman", executable="podman")

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
            if cmd != contents[-1] and cmd[-1] != '\\': # ignore line that end in an escape
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
            ln += f"{parts[0]}=\"{env.lstrip(parts[0]).strip(' ')}\""
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
            ln += f"{parts[0]}=\"{label.lstrip(parts[0]).strip(' ')}\""
            # add '\\' to all but the last line
            if label != contents[-1]:
                ln += " \\"
            ret.append(ln)
        return ret

    def _entry(self, contents: list[str]) -> list[str]:
        return ["", "ENTRYPOINT {}".format(contents[0].split())]

    def generate_build_cmd(self, src: str, dest: str, args: list = None) -> str:
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
        return " ".join(_ for _ in cmd) + ";"

    def format_image_name(self, path: Path, tag: str) -> str:
        return "{}{}{}".format("localhost/" if "/" not in tag else "", tag, ":latest" if ":" not in tag else "")

    def clean_up_old_image_tag(self, name: str) -> str:
        return "podman rmi {}".format(name)

    def build_exists(self, name: str) -> bool:
        return False

    def generate_final_image_cmd(self, src: str, dest: str) -> str:
        return "{} tag {} {}".format(self.executable, src, dest)


class Apptainer(Backend):
    """Apptainer backend."""

    def __init__(self):
        super().__init__(name="apptainer", executable="apptainer")

    def _from(self, contents: list[str]) -> list[str]:
        ret: list[str] = list()
        if re_match(r"^.*\.sif$", contents[0]):
            ret.append("Bootstrap: localimage")
        elif re_match(r"^.*\/.*:.*$", contents[0]):
            ret.append("Bootstrap: docker")
        else:
            raise TemplateSyntaxError("Unknown source format in @from!", contents[0])
        ret.append("From: {}".format(contents[0]))
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

    def generate_build_cmd(self, src: str, dest: str, args: list = None) -> str:
        cmd: list[str] = ["{} build".format(self.executable)]
        # arguments
        if args is not None and len(args) > 0:
            cmd.append(" ".join(_ for _ in args) if args is not None else "")
        # destination
        cmd.append("{}".format(dest))
        # script
        cmd.append("{}".format(src))
        return " ".join(_ for _ in cmd) + ";"

    def format_image_name(self, path: Path, tag: str) -> str:
        return "{}{}".format(Path.joinpath(path, tag), ".sif" if ".sif" not in tag else "")

    def clean_up_old_image_tag(self, name: str) -> str:
        return "echo"

    def build_exists(self, name: str) -> bool:
        if Path(name).is_file():
            return True
        return False

    def generate_final_image_cmd(self, src: str, dest: str) -> str:
        return "cp {} {}".format(src, dest)


def get_backend() -> Backend:
    backend = config.get("velocity:backend")
    if backend == "podman":
        b = Podman()
    elif backend == "apptainer":
        b = Apptainer()
    else:
        raise BackendNotSupported(backend)

    # check that backend is available
    if b.is_available():
        return b
    else:
        raise BackendNotAvailable("Your system does not have the '{}' backend".format(b.name))
