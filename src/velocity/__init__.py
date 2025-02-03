from colorama import Fore, Style
from loguru import logger; logger.disable("velocity")  # noqa: E702 # disable logging at the module level

from velocity._config import config  # noqa: E402
from velocity._graph import ImageRepo  # noqa: E402
from velocity._build import ImageBuilder  # noqa: E402
from velocity._print import TextBlock, header_print, indent_print  # noqa: E402


# config functions
def get_system() -> str:
    """Get the system."""

    return config.get("velocity:system")


def set_system(system: str) -> None:
    """Set the system."""

    config.set("velocity:system", str(system))


def get_backend() -> str:
    """Get the backend."""

    return config.get("velocity:backend")


def set_backend(backend: str) -> None:
    """Set the backend."""

    config.set("velocity:backend", str(backend))


def get_distro() -> str:
    """Get the distro."""

    return config.get("velocity:distro")


def set_distro(distro: str) -> None:
    """Set the distro."""

    config.set("velocity:distro", str(distro))


def build(
    specs: str,
    name: str = None,
    dry_run: bool = False,
    leave_tags: bool = False,
    verbose: bool = False,
    clean: bool = False,
) -> None:
    """Build an image from a spec string."""

    imageRepo = ImageRepo()
    for p in config.get("velocity:image_path").strip(":").split(":"):
        imageRepo.import_from_dir(p)

    # get recipe
    recipe = imageRepo.create_build_recipe(specs.split())[0]

    # print build specs
    header_print([TextBlock("Build Order:")])
    for r in recipe:
        indent_print([TextBlock(f"{r.name}@{r.version}-{r.id}", fore=Fore.MAGENTA, style=Style.BRIGHT)])
    print()  # newline

    # prep builder
    builder = ImageBuilder(
        recipe, build_name=name, dry_run=dry_run, remove_tags=leave_tags, verbose=verbose, clean_build_dir=clean
    )

    # build
    builder.build()


# visible attributes
__all__ = ["get_system", "set_system", "get_backend", "set_backend", "get_distro", "set_distro", "build"]
