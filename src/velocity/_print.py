"""Printing formatter."""

from colorama import Fore, Back, Style


class TextBlock:
    """Defines a block of text and its styling."""

    def __init__(
        self,
        text: str,
        fore: Fore = Fore.RESET,
        back: Back = Back.RESET,
        style: Style = Style.NORMAL,
    ) -> None:
        self.text = text
        self.fore = fore
        self.back = back
        self.style = style


def bare_print(tb: list[TextBlock]) -> None:
    """Print a list of TextBlocks."""
    for text_block in tb:
        print(
            "{}{}{}{}{}".format(
                text_block.fore,
                text_block.back,
                text_block.style,
                text_block.text,
                Style.RESET_ALL,
            ),
            end="",
        )
    # print a newline at the end
    print()


def header_print(tb: list[TextBlock]) -> None:
    """Print a list of TextBlocks with a preceding '==> ' block."""
    text_blocks = [TextBlock("==> ", fore=Fore.GREEN, style=Style.BRIGHT)]
    text_blocks.extend(tb)
    bare_print(text_blocks)


def indent_print(tb: list[TextBlock]) -> None:
    """Print a list of TextBlocks with a preceding 4 spaces."""
    text_blocks = [TextBlock("    ", fore=Fore.GREEN, style=Style.BRIGHT)]
    text_blocks.extend(tb)
    bare_print(text_blocks)
