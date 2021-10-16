import pkg_resources
import argparse
from itertools import chain
from typing import Iterable, Dict, Tuple, Union, IO, Set
from .utilities import (
    get_required_distribution_names,
    get_installed_distributions,
    iter_file_requirement_strings,
    reinstall_editable,
    get_requirement_string_distribution_name,
    normalize_name,
)
from ..utilities import iter_parse_delimited_values


def get_frozen_requirements(
    requirement_strings: Iterable[str] = (),
    requirement_files: Iterable[Union[str, IO[str]]] = (),
    exclude: Iterable[str] = (),
) -> Tuple[str, ...]:
    """
    Get the (pinned) requirements for one or more packages/requirements.

    Parameters:

    - requirement_strings ([str])
    - requirement_files ([str|typing.IO]): File paths or file objects
      representing requirements files
    - exclude ([str]): One or more distributions to exclude/ignore.
      Note: Excluding a distribution excludes all requirements which would
      be identified through recursively.
      those requirements occur elsewhere.
    """
    reinstall_editable()
    if isinstance(requirement_strings, str):
        requirement_strings = (requirement_strings,)
    if isinstance(requirement_files, (str, IO)):
        requirement_files = (requirement_files,)
    name: str
    return tuple(
        sorted(
            _iter_frozen_requirements(
                chain(
                    requirement_strings,
                    *map(iter_file_requirement_strings, requirement_files),
                ),
                exclude=set(
                    map(get_requirement_string_distribution_name, exclude)
                ),
                exclude_recursive=set(map(normalize_name, exclude)),
            ),
            key=lambda name: name.lower(),
        )
    )


def _iter_frozen_requirements(
    requirement_strings: Iterable[str],
    exclude: Set[str],
    exclude_recursive: Set[str],
) -> Iterable[str]:
    if isinstance(requirement_strings, str):
        requirement_strings = (requirement_strings,)
    installed_distributions: Dict[
        str, pkg_resources.Distribution
    ] = get_installed_distributions()

    def get_requirement_string(distribution_name: str) -> str:
        distribution: pkg_resources.Distribution = installed_distributions[
            distribution_name
        ]
        return str(distribution.as_requirement())

    def get_required_distribution_names_(requirement_string: str) -> Set[str]:
        name: str = get_requirement_string_distribution_name(
            requirement_string
        )
        if name in exclude_recursive:
            return set()
        required_distribution_names: Set[
            str
        ] = get_required_distribution_names(
            requirement_string, exclude=exclude_recursive
        )
        if name not in exclude:
            required_distribution_names.add(name)
        return required_distribution_names

    return map(
        get_requirement_string,
        set(
            chain(*map(get_required_distribution_names_, requirement_strings))
        ),
    )


def freeze(
    requirement_strings: Iterable[str] = (),
    requirement_files: Iterable[Union[str, IO[str]]] = (),
    exclude: Iterable[str] = (),
) -> None:
    print(
        "\n".join(
            get_frozen_requirements(
                requirement_strings=requirement_strings,
                requirement_files=requirement_files,
                exclude=exclude,
            )
        )
    )


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="daves-dev-tools requirements freeze"
    )
    parser.add_argument(
        "requirement_specifier",
        nargs="+",
        type=str,
        help="One or more requirement specifiers",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        default=[],
        type=str,
        action="append",
        help=(
            "A comma-separated list of distributions to exclude from the "
            "output. Please note that excluding a distribution also excludes "
            "any/all requirements which might be recursively discovered "
            "for that package."
        ),
    )
    parser.add_argument(
        "-r",
        "--requirement",
        default=[],
        type=str,
        action="append",
        help=("The local file path of a requirements file"),
    )
    arguments: argparse.Namespace = parser.parse_args()
    freeze(
        requirement_strings=arguments.requirement_specifier,
        requirement_files=arguments.requirement,
        exclude=tuple(iter_parse_delimited_values(arguments.exclude)),
    )


if __name__ == "__main__":
    main()
