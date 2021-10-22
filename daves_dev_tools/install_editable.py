import argparse
import re
import sys
import os
from pipes import quote
from typing import Iterable, Set, List, Tuple, Pattern
from .requirements.utilities import (
    get_installed_distributions,
    get_requirements_required_distribution_names,
    is_editable,
    normalize_name,
    get_setup_distribution_name,
    is_installed,
)
from .utilities import run, iter_parse_delimited_values


_SETUP_NAMES: Set[str] = {"setup.cfg", "setup.py"}
EXCLUDE_DIRECTORY_REGULAR_EXPRESSIONS: Tuple[str, ...] = (
    r"^[.~].*$",
    r"^venv$",
    r"^site-packages$",
)


def _install_distribution(
    name: str, directory: str, dry_run: bool = False
) -> None:
    is_installed_: bool = is_installed(name)
    if is_installed_ and is_editable(name):
        print(f'"{name}" is already installed in {directory}')
    else:
        command: str
        if is_installed_:
            command = (
                f"{quote(sys.executable)} -m pip uninstall "
                f"-y {quote(name)}"
            )
        else:
            command = (
                f"{quote(sys.executable)} -m pip install "
                f"-e {quote(directory)}"
            )
        if dry_run:
            print(command)
        else:
            run(command)


def find_and_install_distributions(
    distribution_names: Set[str],
    directories: Iterable[str] = ("../"),
    exclude_directory_regular_expressions: Iterable[
        str
    ] = EXCLUDE_DIRECTORY_REGULAR_EXPRESSIONS,
    dry_run: bool = False,
) -> None:
    if isinstance(directories, str):
        directories = (directories,)
    directories = map(os.path.abspath, directories)
    exclude_directory_patterns: Tuple[Pattern, ...] = tuple(
        map(re.compile, exclude_directory_regular_expressions)
    )

    def include_directory(directory: str) -> bool:
        directory_basename: str = os.path.basename(directory)
        for exclude_directory_pattern in exclude_directory_patterns:
            if exclude_directory_pattern.match(directory_basename):
                return False
        return True

    def find_and_install_directory_distributions(directory: str) -> None:
        sub_directories: List[str]
        files: List[str]
        sub_directories, files = next(iter(os.walk(directory)))[1:3]

        def get_subdirectory_path(subdirectory: str) -> str:
            return os.path.join(directory, subdirectory)

        sub_directories = list(map(get_subdirectory_path, sub_directories))
        # Check to see if this is a project directory
        if any(map(_SETUP_NAMES.__contains__, map(str.lower, files))):
            name: str = get_setup_distribution_name(directory)
            if name in distribution_names:
                _install_distribution(name, directory, dry_run)
        else:
            list(
                map(
                    find_and_install_directory_distributions,
                    filter(include_directory, sub_directories),
                )
            )

    list(map(find_and_install_directory_distributions, directories))


def install_editable(
    requirements: Iterable[str] = (),
    directories: Iterable[str] = ("../"),
    exclude: Iterable[str] = (),
    exclude_directory_regular_expressions: Iterable[
        str
    ] = EXCLUDE_DIRECTORY_REGULAR_EXPRESSIONS,
    dry_run: bool = False,
) -> None:
    """
    Install, in editable/develop mode, all distributions, except for those
    specified in `exclude`, which are required for the specified
    `requirements`.

    Parameters:
    - requirements ([str]) = ():
      One or more requirement specifiers or configuration file paths to which
      installation should be limited
    - directories ([str]) = ("../",): The directories in which to search
      for distributions to install. By default, the parent of the currently
      directory is used.
    - exclude ([str]): One or more distributions to pass over when searching
      for distributable projects
    """
    required_distribution_names: Set[str] = (
        get_requirements_required_distribution_names(requirements)
        if requirements
        else set(get_installed_distributions().keys())
    )
    find_and_install_distributions(
        distribution_names=(
            set(
                map(
                    normalize_name,
                    get_requirements_required_distribution_names(
                        required_distribution_names
                    ),
                )
            )
            - set(map(normalize_name, exclude))
        ),
        directories=directories,
        exclude_directory_regular_expressions=(
            exclude_directory_regular_expressions
        ),
        dry_run=dry_run,
    )


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="daves-dev-tools install-editable",
        description=(
            "This command will attempt to find and install, in "
            "develop (editable) mode, all packages which are "
            "installed in the current python environment. If one or "
            "more `requirement` file paths or specifiers are provided, "
            "installation will be limited to the dependencies identified "
            "(recursively) by these requirements. Exclusions can be specified "
            "using the `-e` parameter. Directories can be excluded by "
            "passing regular expressions to the `-edre` parameter."
        ),
    )
    parser.add_argument(
        "requirement",
        nargs="*",
        type=str,
        default=[],
        help=(
            "One or more requirement specifiers or configuration file paths. "
            "If provided, only dependencies of these requirements will be "
            "installed."
        ),
    )
    parser.add_argument(
        "-d",
        "--directory",
        default=["../"],
        type=str,
        action="append",
        help=(
            "A directory in which to search for requirements. "
            "By default, the directory above the current directory is "
            "searched. This argument may be passed more than once to include "
            "multiple locations."
        ),
    )
    parser.add_argument(
        "-e",
        "--exclude",
        default=[],
        type=str,
        action="append",
        help="A comma-separated list of distribution names to exclude",
    )

    parser.add_argument(
        "-edre",
        "--exclude-directory-regular-expression",
        default=list(EXCLUDE_DIRECTORY_REGULAR_EXPRESSIONS),
        type=str,
        action="append",
        help=(
            "Directories matching this regular expression will be excluded "
            "when searching for setup locations This argument may be passed "
            "more than once to exclude directories matching more than one "
            "regular expression. The default for this argument is "
            "equivalent to `-edre {}`".format(
                " -edre ".join(
                    map(quote, EXCLUDE_DIRECTORY_REGULAR_EXPRESSIONS)
                )
            )
        ),
    )
    parser.add_argument(
        "-dr",
        "--dry-run",
        default=False,
        action="store_const",
        const=True,
        help=("Print, but do not execute, all `pip install` commands"),
    )
    arguments: argparse.Namespace = parser.parse_args()
    install_editable(
        requirements=arguments.requirement,
        directories=arguments.directory,
        exclude_directory_regular_expressions=(
            arguments.exclude_directory_regular_expression
        ),
        exclude=iter_parse_delimited_values(arguments.exclude),
        dry_run=arguments.dry_run,
    )


if __name__ == "__main__":
    main()
