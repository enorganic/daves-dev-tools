import sys
from importlib import import_module
from types import ModuleType
from . import __name__ as _module_name
from .errors import get_exception_text


def _print_help() -> None:
    print(
        "Usage:\n"
        "  daves-dev-tools <command> [options]\n\n"
        "Commands:\n"
        "  git                         Tools for interacting with git repos.\n"
        "  requirements                Tools for managing requirement "
        "versions.\n"
        "  install-editable            Auto-discover and install packages "
        'in "develop"\n'
        "                              mode used by the current environment "
        "or by one or\n"
        "                              more specified packages/projects.\n"
        "  make-typed                  Configure your project to indicate to "
        "`mypy` that\n"
        "                              the contents are type-hinted.\n"
        "  uninstall-all               Uninstall all distributions from the "
        "current\n"
        "                              python environment except for those "
        "explicitly\n"
        "                              specified (and their dependencies).\n"
        "  clean                       Delete files from your project which "
        "are ignored\n"
        "                              by `git`, excepting files matching "
        "specified\n"
        "                              exclusion patterns.\n"
        "  distribute                  Build and distribute to PYPI (or other "
        "indexes)\n"
        "                              with one command."
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
