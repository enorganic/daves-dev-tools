import pkg_resources
import argparse
from itertools import chain
from typing import Iterable, Dict, Tuple, Set
from more_itertools import unique_everseen
from .utilities import (
    get_required_distribution_names,
    get_installed_distributions,
    iter_configuration_file_requirement_strings,
    reinstall_editable,
    get_requirement_string_distribution_name,
    normalize_name,
    is_configuration_file,
)
from ..utilities import iter_parse_delimited_values


def get_frozen_requirements(
    requirements: Iterable[str] = (),
    exclude: Iterable[str] = (),
) -> Tuple[str, ...]:
    """
    Get the (frozen) requirements for one or more specified distributions or
    configuration files.

    Parameters:

    - requirements ([str]): One or more requirement specifiers (for example:
      "requirement-name[extra-a,extra-b]" or ".[extra-a, extra-b]) and/or paths
      to a setup.cfg, pyproject.toml, tox.ini or requirements.txt file
    - exclude ([str]): One or more distributions to exclude/ignore.
      Note: Excluding a distribution excludes all requirements which would
      be identified through recursively.
      those requirements occur elsewhere.
    """
    # Separate requirement strings from requirement files
    if isinstance(requirements, str):
        requirements = {requirements}
    else:
        requirements = set(requirements)
    requirement_files: Set[str] = set(
        filter(is_configuration_file, requirements)
    )
    requirement_strings: Set[str] = requirements - requirement_files
    reinstall_editable()
    name: str
    return tuple(
        sorted(
            _iter_frozen_requirements(
                unique_everseen(
                    chain(
                        requirement_strings,
                        *map(
                            iter_configuration_file_requirement_strings,
                            requirement_files,
                        ),
                    )
                ),
                exclude=set(
                    map(
                        get_requirement_string_distribution_name,
                        requirement_strings,
                    )
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

    def not_excluded(name: str) -> bool:
        return name not in exclude

    return map(
        get_requirement_string,
        unique_everseen(
            chain(*map(get_required_distribution_names_, requirement_strings)),
        ),
    )


def freeze(
    requirements: Iterable[str] = (),
    exclude: Iterable[str] = (),
) -> None:
    """
    Print the (frozen) requirements for one or more specified requirements or
    configuration files.

    Parameters:

    - requirements ([str]): One or more requirement specifiers (for example:
      "requirement-name[extra-a,extra-b]" or ".[extra-a, extra-b]) and/or paths
      to a setup.cfg, pyproject.toml, tox.ini or requirements.txt file
    - exclude ([str]): One or more distributions to exclude/ignore.
      Note: Excluding a distribution excludes all requirements which would
      be identified through recursively.
      those requirements occur elsewhere.
    """
    print(
        "\n".join(
            get_frozen_requirements(
                requirements=requirements,
                exclude=exclude,
            )
        )
    )


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="daves-dev-tools requirements freeze"
    )
    parser.add_argument(
        "requirement",
        nargs="+",
        type=str,
        help="One or more requirement specifiers or configuration file paths",
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
    arguments: argparse.Namespace = parser.parse_args()
    freeze(
        requirements=arguments.requirement,
        exclude=tuple(iter_parse_delimited_values(arguments.exclude)),
    )


if __name__ == "__main__":
    main()
