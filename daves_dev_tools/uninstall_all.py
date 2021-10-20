import argparse
import sys
from itertools import chain
from typing import Iterable, Set
from more_itertools import unique_everseen
from .requirements.utilities import (
    get_installed_distributions,
    get_required_distribution_names,
    iter_configuration_file_requirement_strings,
    reinstall_editable,
    get_requirement_string_distribution_name,
    is_configuration_file,
)
from .utilities import run


def get_requirements_required_distribution_names(
    requirements: Iterable[str] = (),
) -> Set[str]:
    """
    Get the distributions required by one or more specified distributions or
    configuration files.

    Parameters:

    - requirements ([str]): One or more requirement specifiers (for example:
      "requirement-name[extra-a,extra-b]" or ".[extra-a, extra-b]) and/or paths
      to a setup.cfg, pyproject.toml, tox.ini or requirements.txt file
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
    return set(
        sorted(
            _iter_requirement_strings_required_distribution_names(
                unique_everseen(
                    chain(
                        requirement_strings,
                        *map(
                            iter_configuration_file_requirement_strings,
                            requirement_files,
                        ),
                    )
                )
            ),
            key=lambda name: name.lower(),
        )
    )


def _iter_requirement_strings_required_distribution_names(
    requirement_strings: Iterable[str],
) -> Iterable[str]:
    if isinstance(requirement_strings, str):
        requirement_strings = (requirement_strings,)

    def get_required_distribution_names_(requirement_string: str) -> Set[str]:
        try:
            name: str = get_requirement_string_distribution_name(
                requirement_string
            )
            return get_required_distribution_names(requirement_string) | {name}
        except KeyError:
            return set()

    return unique_everseen(
        chain(*map(get_required_distribution_names_, requirement_strings)),
    )


def uninstall_all(exclude: Iterable[str] = (), dry_run: bool = False) -> None:
    """
    Uninstall all distributions except for those requirementS specified
    in `exclude`.

    Parameters:

    - exclude ([str]): One or more requirement specifiers (for example:
      "requirement-name[extra-a,extra-b]" or ".[extra-a, extra-b]) and/or paths
      to a setup.cfg, pyproject.toml, tox.ini or requirements.txt file
    """
    name: str
    uninstall_distribution_names: str = " ".join(
        sorted(
            (
                set(get_installed_distributions().keys())
                - get_requirements_required_distribution_names(
                    chain(
                        ("pip", "setuptools", "wheel", "distribute"), exclude
                    )
                )
            ),
            key=lambda name: name.lower(),
        )
    )
    command: str = (
        f"{sys.executable} -m pip uninstall -y {uninstall_distribution_names}"
    )
    if dry_run:
        print(command)
    else:
        run(command, echo=True)


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="daves-dev-tools uninstall-all",
        description=(
            "This command will uninstall all distributions "
            "installed in the same environment as that from which this "
            "command is executed, excluding any specified by "
            "`--exclude EXCLUDE`"
        ),
    )
    parser.add_argument(
        "-e",
        "--exclude",
        default=[],
        type=str,
        action="append",
        help=(
            "One or more distribution specifiers, requirement files, "
            "setup.cfg files, pyproject.toml files, or tox.ini files "
            "denoting packages to exclude (along with all of their "
            "requirements) from those distributions to be "
            "uninstalled"
        ),
    )
    parser.add_argument(
        "-dr",
        "--dry-run",
        default=False,
        const=True,
        action="store_const",
        help=(
            "Print, but do not execute, the assembled `pip uninstall` command "
            "which, absent this flag, would be executed"
        ),
    )
    arguments: argparse.Namespace = parser.parse_args()
    uninstall_all(exclude=arguments.exclude, dry_run=arguments.dry_run)


if __name__ == "__main__":
    main()
