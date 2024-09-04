import re
from hashlib import sha256
from pathlib import Path
from abc import ABC, abstractmethod
from ._exceptions import (UndefinedVariableInTemplate, RepeatedSection, LineOutsideOfSection, TemplateSyntaxError,
                         BackendNotSupported)
from ._config import config


def _substitute(text: str, variables: dict, regex: str) -> str:
    def _replace(m: re.Match):
        """
            Substitute a variables in a string by a regex.
        """
        if m.group(1) in variables:
            return str(variables[m.group(1)])
        else:
            raise UndefinedVariableInTemplate(m.group(1))

    return re.sub(regex, _replace, text)


class Backend(ABC):

    def __init__(self, name: str, variables: dict = None) -> None:
        self.name = name
        self.variables = {
            '__backend__': config.get("velocity:backend"),
            '__system__': config.get("velocity:system"),
            '__distro__': config.get("velocity:distro")
        }
        if variables is not None:
            self.variables.update(variables)
        self.template_sections = [
            '@from',
            '@pre',
            '@arg',
            '@copy',
            '@run',
            '@env',
            '@label',
            '@entry',
            '@post'
        ]

    @abstractmethod
    def generate_script(self, file: Path, variables: dict) -> list:
        """
        Generate a build script e.g. .dockerfile/.def
        """
        pass

    @abstractmethod
    def generate_build_cmd(self, src: str, dest: str, args: list = None) -> str:
        """
        Generate CLI command to build image
        """
        pass

    @abstractmethod
    def format_image_name(self, path: Path, tag: str) -> str:
        pass

    @abstractmethod
    def clean_up_old_image_cmd(self, name: str) -> str:
        pass

    def _get_sections(self, template: list) -> dict:
        sections = dict()

        past_sections = list()
        current_section = None

        for line in template:
            if line in self.template_sections:
                if current_section is not None:
                    past_sections.append(current_section)

                if line in past_sections:
                    raise RepeatedSection(line)
                else:
                    current_section = line
                    if current_section not in sections:
                        sections[current_section] = list()
            else:
                if current_section is None:
                    raise LineOutsideOfSection
                else:
                    sections[current_section].append(line)

        return sections

    def _load_template(self, file: Path, variables: dict) -> list:
        variables.update(self.variables)
        template = list()
        with open(file, 'r') as file:
            contents = file.readlines()
            variables.update({'__hash__': sha256(''.join(contents).encode('utf-8')).hexdigest()})
            for line in contents:
                sf_con = self._filter_content(
                    _substitute(
                        line,
                        variables,
                        r'(?<!\\)%{{\s*(\w+)\s*}}'
                    )
                )
                if sf_con != '':
                    template.append(sf_con)
        return template

    def _filter_content(self, text: str) -> str:
        # remove comments, newlines, and superfluous white space
        t = re.sub(r'#.*', '', text)
        t = re.sub(f'\n', '', t)
        t = t.strip(' ')

        # is this line needed for this backend?
        if t == '':
            return ''
        elif t[0] == '?' and f'?{self.name}' not in t:
            return ''
        else:
            return re.sub(r'\?\w*', '', t).strip(' ')


class Podman(Backend):

    def __init__(self, variables: dict):
        super().__init__(name='podman', variables=variables)

    def generate_script(self, file: Path, variables: dict) -> list:
        script = list()
        template = self._load_template(file, variables)
        sections = self._get_sections(template)

        # @from
        if '@from' not in sections:
            raise TemplateSyntaxError("You must have a '@from' section in your template!")
        elif len(sections['@from']) != 1:
            raise TemplateSyntaxError("You can only have one source in your template!", )
        elif len(sections['@from'][0].split()) != 1:
            raise TemplateSyntaxError("Your source must be a single string!", sections['@from'][0])
        else:
            script.append(f"FROM {sections['@from'][0]}")

        # @arg
        vbs = dict()
        if '@arg' in sections:
            if len(sections['@arg']) > 0:
                script.append('')
                for a in sections['@arg']:
                    if len(a.split()) != 1:
                        raise TemplateSyntaxError("Arguments cannot have spaces in their names!")
                    else:
                        script.append(f'ARG {a}')
                        vbs[a] = f'${a}'
        for si in sections.keys():
            for li in range(len(sections[si])):
                sections[si][li] = _substitute(sections[si][li], vbs, r'(?<!\\)@\((\w*)\)')

        # @copy
        if '@copy' in sections:
            if len(sections['@copy']) > 0:
                script.append('')
                for ln in sections['@copy']:
                    if len(ln.split()) != 2:
                        raise TemplateSyntaxError("Your '@copy' can only have one source and destination!", ln)
                    script.append(f"COPY {ln}")

        if '@run' in sections:
            if len(sections['@run']) > 0:
                script.append('')
                for cmd in sections['@run']:
                    ln = ''
                    if cmd == sections['@run'][0]:
                        ln += 'RUN '
                    else:
                        ln += '    '
                    ln += cmd
                    if cmd != sections['@run'][-1]:
                        ln += ' && \\'
                    script.append(ln)

        if '@env' in sections:
            if len(sections['@env']) > 0:
                script.append('')
                for env in sections['@env']:
                    parts = env.split()
                    ln = ''
                    if env == sections['@env'][0]:
                        ln += 'ENV '
                    else:
                        ln += '    '
                    ln += f"{parts[0]}=\"{env.lstrip(parts[0]).strip(' ')}\""
                    if env != sections['@env'][-1]:
                        ln += ' \\'
                    script.append(ln)

        if '@label' in sections:
            if len(sections['@label']) > 0:
                script.append('')
                for label in sections['@label']:
                    parts = label.split()
                    if len(parts) != 2:
                        raise TemplateSyntaxError("Labels must have two parts!", label)
                    ln = ''
                    if label == sections['@label'][0]:
                        ln += 'LABEL '
                    else:
                        ln += '    '
                    ln += f"{parts[0]}=\"{label.lstrip(parts[0]).strip(' ')}\""
                    if label != sections['@label'][-1]:
                        ln += ' \\'
                    script.append(ln)

        if '@entry' in sections:
            if len(sections['@entry']) != 1:
                raise TemplateSyntaxError("You must have one and only one entrypoint!")
            else:
                script.append('')
                script.append(f"ENTRYPOINT {str(sections['@entry'][0].split())}")

        script.append('')

        return script

    def generate_build_cmd(self, src: str, dest: str, args: list = None) -> str:
        arguments = ' ' + ' '.join(
            _ for _ in args
        ) if args is not None else ''
        script = f' -f {src}'
        destination = f' -t {dest}'
        end = ' .;'

        cmd = ['podman build', arguments, script, destination, end]
        return ''.join(_ for _ in cmd)

    def format_image_name(self, path: Path, tag: str) -> str:
        return f"{'localhost/' if '/' not in tag else ''}{tag}{':latest' if ':' not in tag else ''}"

    def clean_up_old_image_cmd(self, name: str) -> str:
        return f'podman untag {name}'


class Apptainer(Backend):

    def __init__(self, variables: dict):
        super().__init__(name='apptainer', variables=variables)

    def generate_script(self, file: Path, variables: dict) -> list:
        script = list()
        template = self._load_template(file, variables)
        sections = self._get_sections(template)

        if '@arg' in sections:
            if len(sections['@arg']) > 0:
                vbs = dict()
                for a in sections['@arg']:
                    if len(a.split()) != 1:
                        raise TemplateSyntaxError("Arguments cannot have spaces in their names!")
                    else:
                        vbs[a] = '{{ ' + a + ' }}'

                for si in sections.keys():
                    for li in range(len(sections[si])):
                        sections[si][li] = _substitute(sections[si][li], vbs, r'(?<!\\)@\((\w*)\)')

        if '@from' not in sections:
            raise TemplateSyntaxError("You must have a '@from' section in your template!")
        elif len(sections['@from']) != 1:
            raise TemplateSyntaxError("You can only have one source in your template!", )
        elif len(sections['@from'][0].split()) != 1:
            raise TemplateSyntaxError("Your source must be a single string!", sections['@from'][0])
        else:
            if re.match(r'^.*\.sif$', sections['@from'][0]):  #Path(sections['@from'][0]).is_file():
                script.append('Bootstrap: localimage')
            elif re.match(r'^.*\/.*:.*$', sections['@from'][0]):
                script.append('Bootstrap: docker')
            else:
                raise TemplateSyntaxError("Unknown source format!", sections['@from'][0])
            script.append(f"From: {sections['@from'][0]}")

        if '@pre' in sections:
            if len(sections['@pre']) > 0:
                script.append('')
                for ln in sections['@pre']:
                    script.append(ln.lstrip('|'))

        if '@copy' in sections:
            if len(sections['@copy']) > 0:
                script.append('')
                script.append('%files')
                for ln in sections['@copy']:
                    if len(ln.split()) != 2:
                        raise TemplateSyntaxError("Your '@copy' can only have one source and destination!", ln)
                    script.append(f"    {ln}")

        if '@run' in sections:
            if len(sections['@run']) > 0:
                script.append('')
                script.append('%post')
                for cmd in sections['@run']:
                    script.append(f'    {cmd}')

        if '@env' in sections:
            if len(sections['@env']) > 0:
                script.append('')
                script.append('%environment')
                for env in sections['@env']:
                    parts = env.split()
                    script.append(f"    export {parts[0]}=\"{env.lstrip(parts[0]).strip(' ')}\"")

        if '@label' in sections:
            if len(sections['@label']) > 0:
                script.append('')
                script.append('%labels')
                for label in sections['@label']:
                    parts = label.split()
                    script.append(f"    {parts[0]} {label.lstrip(parts[0]).strip(' ')}")

        if '@entry' in sections:
            if len(sections['@entry']) != 1:
                raise TemplateSyntaxError("You must have one and only one entrypoint!")
            else:
                script.append('')
                script.append('%runscript')
                script.append(f"    {sections['@entry'][0]}")

        if '@post' in sections:
            if len(sections['@post']) > 0:
                script.append('')
                for ln in sections['@post']:
                    script.append(ln.lstrip('|'))

        script.append('')

        return script

    def generate_build_cmd(self, src: str, dest: str, args: list = None) -> str:
        arguments = ' ' + ' '.join(
            x for x in args
        ) if args is not None else ''
        script = f' {src}'
        destination = f' {dest}'
        end = ';'

        cmd = ['apptainer build', arguments, destination, script, end]
        return ''.join(_ for _ in cmd)

    def format_image_name(self, path: Path, tag: str) -> str:
        return f"{Path.joinpath(path, tag)}{'.sif' if '.sif' not in tag else ''}"

    def clean_up_old_image_cmd(self, name: str) -> str:
        return 'echo'


def get_backend(variables: dict) -> Backend:
    backend = config.get("velocity:backend")
    if backend == 'podman':
        return Podman(variables)
    elif backend == 'apptainer':
        return Apptainer(variables)
    else:
        raise BackendNotSupported(backend)
