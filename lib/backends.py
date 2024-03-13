import re
from hashlib import sha256
from pathlib import Path
from lib.exceptions import *
from abc import ABC, abstractmethod
from os.path import expandvars


class Backend(ABC):

    def __init__(self, name: str, variables: dict = None) -> None:
        self.name = name
        self.variables = {
            '': '%',
            '__backend__': self.name
        }
        if variables is not None:
            self.variables.update(variables)
        self.template_sections = [
            '@from',
            '@copy',
            '@run',
            '@env',
            '@label',
            '@entry'
        ]

    @abstractmethod
    def generate_script(self, file: Path, variables: dict) -> list:
        pass

    @abstractmethod
    def generate_build_cmd(self, src: str, dest: str, args: list = None) -> str:
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
        template = list()
        with open(file, 'r') as file:
            contents = file.readlines()
            variables.update({'__hash__': sha256(''.join(contents).encode('utf-8')).hexdigest()})
            for line in contents:
                sf_con = self._filter_content(self._substitute(line, variables))
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

    def _substitute(self, text: str, variables: dict) -> str:
        variables.update(self.variables)

        def _replace(m: re.Match):
            """
                Substitute a template variable.
            """
            if m.group(1) in variables:
                evaluated = str(expandvars(f"{str(variables[m.group(1)])}"))
                return str(evaluated)
            else:
                raise UndefinedVariableInTemplate(m.group(1))

        return re.sub(r'%(\w*)%', _replace, text)


class Podman(Backend):

    def __init__(self, variables: dict):
        super().__init__(name='podman', variables=variables)

    def generate_script(self, file: Path, variables: dict) -> list:
        script = list()
        template = self._load_template(file, variables)
        sections = self._get_sections(template)

        if '@from' not in sections:
            raise TemplateSyntaxError("You must have a '@from' section in your template!")
        elif len(sections['@from']) != 1:
            raise TemplateSyntaxError("You can only have one source in your template!",)
        elif len(sections['@from'][0].split()) != 1:
            raise TemplateSyntaxError("Your source must be a single string!", sections['@from'][0])
        else:
            script.append(f"FROM {sections['@from'][0]}")

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


class Apptainer(Backend):

    def __init__(self, variables: dict):
        super().__init__(name='apptainer', variables=variables)

    def generate_script(self, file: Path, variables: dict) -> list:
        script = list()
        template = self._load_template(file, variables)
        sections = self._get_sections(template)

        if '@from' not in sections:
            raise TemplateSyntaxError("You must have a '@from' section in your template!")
        elif len(sections['@from']) != 1:
            raise TemplateSyntaxError("You can only have one source in your template!", )
        elif len(sections['@from'][0].split()) != 1:
            raise TemplateSyntaxError("Your source must be a single string!", sections['@from'][0])
        else:
            if Path(sections['@from'][0]).is_file():
                script.append('Bootstrap: localimage')
            else:
                script.append('Bootstrap: docker')
            script.append(f"From: {sections['@from'][0]}")

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


def get_backend(name: str, variables: dict) -> Backend:
    if name == 'podman':
        return Podman(variables)
    elif name == 'apptainer':
        return Apptainer(variables)
    else:
        raise BackendNotSupported(name)
