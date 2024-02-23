import re
from typing import TextIO
from lib.exceptions import UndefinedVariableInTemplate


def parse_template(file: TextIO, section: str, variables: dict) -> list[str]:
    content = list()

    # get content from the right section
    current_section = None
    for line in file:
        # ignore comments
        if re.search(r'^\s*#', line) is not None:
            continue
        # find section head
        elif re.search(r'.*\$%\$\s*(\w*)\s*\$%\$.*', line) is not None:
            current_section = re.search(r'.*\$%\$\s*(\w*)\s*\$%\$.*', line)[1]
        # add lines from section to content
        elif current_section == section:
            content.append(line.rstrip('\n'))
        else:
            continue

    def replace(m: re.Match):
        """
        Substitute a template variable.
        """
        if m.group(1) in variables:
            return str(variables[m.group(1)])
        else:
            raise UndefinedVariableInTemplate(m.group(1))

    # substitute variables
    for line in range(len(content)):
        content[line] = re.sub(r'{@\s*(\w*)\s*@}', replace, content[line])

    return content
