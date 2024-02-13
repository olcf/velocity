from colorama import Fore, Back, Style


def h1print(text: str):
    print(Fore.BLUE)
    print('#' * 60)
    print('#', text)
    print('#' * 60)
    print(Fore.RESET, end='')


def p1print(text: str):
    print(Fore.BLUE + '=' + Fore.GREEN + '=' + Fore.RED + '>', Fore.RESET, end='')
    print(text)


def sp1print(text: str):
    print('\t', end='')
    print(text)
