from colorama import Fore, Back, Style


class TextBlock:

    def __init__(self, text: str, fore: Fore = Fore.RESET, back: Back = Back.RESET, style: Style = Style.NORMAL):
        self.text = text
        self.fore = fore
        self.back = back
        self.style = style


def p1print(tb: list[TextBlock]):
    text_blocks = [
        TextBlock('==> ', fore=Fore.LIGHTGREEN_EX, style=Style.BRIGHT)
    ]
    text_blocks.extend(tb)
    print_text_blocks(text_blocks)


def sp1print(tb: list[TextBlock]):
    text_blocks = [
        TextBlock('\t', fore=Fore.LIGHTGREEN_EX, style=Style.BRIGHT)
    ]
    text_blocks.extend(tb)
    print_text_blocks(text_blocks)


def print_text_blocks(text_blocks: list[TextBlock]):
    for text_block in text_blocks:
        print(f'{text_block.fore}{text_block.back}{text_block.style}{text_block.text}{Style.RESET_ALL}', end='')
    print()
