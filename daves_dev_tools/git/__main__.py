import sys
from importlib import import_module
from types import ModuleType
from ..errors import get_exception_text
from . import __name__ as _module_name


def _print_help() -> None:
    print(
        "Usage:\n"
        "  daves-dev-tools git <command> [options]\n\n"
        "Commands:\n"
        "  download                    Download files from a GIT repo "
        "matching one or more\n"
        "                              specified pattern(s).\n"
        "  tag-version                 Tag your repo with the python package "
        "version, if a tag for\n"
        "                              that version doesn't already exist."
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
    except Exception:
        print(get_exception_text())
        _print_help()


if __name__ == "__main__":
    main()
