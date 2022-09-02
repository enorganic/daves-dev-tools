import sys
from importlib import import_module
from types import ModuleType

from . import __name__ as _module_name


def _print_help() -> None:
    print(
        "Usage:\n"
        "  daves-dev-tools requirements <command> [options]\n\n"
        "Commands:\n"
        "  update                      Update requirement versions in the "
        "specified files to\n"
        "                              align with currently installed "
        "versions of each distribution.\n"
        "  freeze                      Print dependencies inferred from an "
        "installed distribution\n"
        "                              or project, in a similar format to the "
        "output of `pip freeze`."
    )


def _get_command() -> str:
    command: str = ""
    if len(sys.argv) > 1:
        command = sys.argv.pop(1).lower().replace("-", "_")
    return command


def main() -> None:
    """
    Run a sub-module `main` function.
    """
    command = _get_command()
    module: ModuleType
    try:
        try:
            module = import_module(f"{_module_name}.{command}.__main__")
        except ImportError:
            module = import_module(f"{_module_name}.{command}")
        module.main()  # type: ignore
    except ImportError:
        _print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
