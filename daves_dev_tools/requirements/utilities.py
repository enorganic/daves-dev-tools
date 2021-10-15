import sys
import os
import pipes
from itertools import chain
import pkg_resources
from typing import Dict, Iterable, Set, Tuple, List, IO, Union
from packaging.utils import canonicalize_name
from packaging.requirements import InvalidRequirement, Requirement
from ..utilities import lru_cache, run

# This variable tracks the absolute file paths from which a package has been
# re-installed, in order to avoid performing a reinstall redundantly
_reinstalled_locations: Set[str] = set()


@lru_cache()
def normalize_name(name: str) -> str:
    """
    Normalize a project/distribution name
    """
    return pkg_resources.safe_name(canonicalize_name(name)).lower()


@lru_cache()
def get_installed_distributions() -> Dict[str, pkg_resources.Distribution]:
    """
    Return a dictionary of installed distributions.
    """
    installed: Dict[str, pkg_resources.Distribution] = {}
    for distribution in pkg_resources.working_set:
        installed[normalize_name(distribution.project_name)] = distribution
    return installed


def get_distribution(name: str) -> pkg_resources.Distribution:
    return get_installed_distributions()[normalize_name(name)]


@lru_cache()
def is_requirement_string(requirement_string: str) -> bool:
    try:
        Requirement(requirement_string)
    except InvalidRequirement:
        return False
    return True


def iter_file_requirement_strings(
    requirement_file: Union[str, IO[str]]
) -> Iterable[str]:
    """
    Read a requirements file and yield the parsed requirements.
    """
    lines: List[str]
    if isinstance(requirement_file, str):
        requirement_file_io: IO[str]
        with open(requirement_file) as requirement_file_io:
            lines = requirement_file_io.readlines()
    else:
        lines = requirement_file.read().split("\n")
    return filter(is_requirement_string, lines)


@lru_cache()
def is_editable(distribution_name: str) -> bool:
    """
    Return `True` if the indicated distribution is an editable installation.
    """
    return _distribution_is_editable(get_distribution(distribution_name))


def _distribution_is_editable(
    distribution: pkg_resources.Distribution,
) -> bool:
    """
    Return `True` if the `distribution` is an editable installation.
    """
    egg_link_file_name: str = f"{distribution.project_name}.egg-link"

    def project_egg_link_exists(path: str) -> bool:
        return os.path.isfile(os.path.join(path, egg_link_file_name))

    return any(map(project_egg_link_exists, sys.path))


def _iter_editable_distributions(
    include: Set[str],
    exclude: Set[str],
    include_locations: Set[str],
    exclude_locations: Set[str],
) -> Iterable[pkg_resources.Distribution]:
    def include_distribution_item(
        name_distribution: Tuple[str, pkg_resources.Distribution]
    ) -> bool:
        name: str
        distribution: pkg_resources.Distribution
        name, distribution = name_distribution
        if (
            ((not include) or (name in include))
            and ((not exclude) or (name not in exclude))
            and (
                (not include_locations)
                or (
                    os.path.abspath(distribution.location)
                    not in include_locations
                )
            )
            and (
                (not exclude_locations)
                or (
                    os.path.abspath(distribution.location)
                    not in exclude_locations
                )
            )
        ):
            return _distribution_is_editable(distribution)
        return False

    return map(
        list.pop,  # type: ignore
        map(
            list,
            filter(
                include_distribution_item,
                get_installed_distributions().items(),
            ),
        ),
    )


def _reinstall_distribution(
    distribution: pkg_resources.Distribution, echo: bool = False
) -> None:
    run(
        (
            f"{pipes.quote(sys.executable)} -m pip install --no-deps "
            f"-e {pipes.quote(distribution.location)}"
        ),
        echo=echo,
    )
    _reinstalled_locations.add(os.path.abspath(distribution.location))


def reinstall_editable(
    include: Iterable[str] = (),
    exclude: Iterable[str] = (),
    include_locations: Iterable[str] = (),
    exclude_locations: Iterable[str] = (),
    echo: bool = False,
) -> None:
    """
    This function re-installs editable distributions.

    Parameters:

    - include ([str]):
      One or more distribution names to include (excluding all others)
    - exclude ([str])
      One or more distribution names to exclude
    - include_locations ([str])
      One or more distribution locations to include (excluding all others)
    - exclude_locations ([str])
      One or more distribution locations to exclude
    - echo (bool): If `True`, the "pip install ..." commands are printed to
      `sys.stdout`
    """
    if isinstance(include, str):
        include = {normalize_name(include)}
    else:
        include = set(map(normalize_name, include))
    if isinstance(exclude, str):
        exclude = {normalize_name(exclude)}
    else:
        exclude = set(map(normalize_name, exclude))
    if isinstance(include_locations, str):
        include_locations = {os.path.abspath(include_locations)}
    else:
        include_locations = set(map(os.path.abspath, include_locations))
    if isinstance(exclude_locations, str):
        exclude_locations = {os.path.abspath(exclude_locations)}
    else:
        exclude_locations = set(map(os.path.abspath, exclude_locations))
    # Don't re-install a location more than once
    exclude_locations |= _reinstalled_locations

    def reinstall_distribution_(
        distribution: pkg_resources.Distribution,
    ) -> None:
        _reinstall_distribution(distribution, echo=echo)

    list(
        map(
            reinstall_distribution_,
            _iter_editable_distributions(
                include, exclude, include_locations, exclude_locations
            ),
        )
    )
    get_installed_distributions.cache_clear()


def get_location_distribution_name(location: str) -> str:
    """
    Get a distribution name based on an installation location
    """
    return _get_location_distribution_name(os.path.abspath(location))


def _get_location_distribution_name(location: str) -> str:
    def _is_in_location(
        name_distribution: Tuple[str, pkg_resources.Distribution]
    ) -> bool:
        return os.path.abspath(name_distribution[1].location) == location

    def _get_name(
        name_distribution: Tuple[str, pkg_resources.Distribution]
    ) -> str:
        return name_distribution[0]

    return next(
        map(
            _get_name,
            filter(_is_in_location, get_installed_distributions().items()),
        )
    )


def _get_package_requirement(
    requirement_string: str,
) -> pkg_resources.Requirement:
    try:
        return pkg_resources.Requirement.parse(requirement_string)
    except (
        getattr(
            pkg_resources, "extern"
        ).packaging.requirements.InvalidRequirement,
        getattr(pkg_resources, "RequirementParseError"),
    ) as error:
        # Try to parse the requirement as an installation target location,
        # such as can be used with `pip install`
        location: str = requirement_string
        extras: str = ""
        if "[" in requirement_string and requirement_string.endswith("]"):
            parts: List[str] = requirement_string.split("[")
            location = "[".join(parts[:-1])
            extras = f"[{parts[-1]}"
        location = os.path.abspath(location)
        try:
            name: str = _get_location_distribution_name(location)
            return pkg_resources.Requirement.parse(f"{name}{extras}")
        except TypeError:
            raise error


def get_required_distribution_names(
    requirement_string: str,
    exclude: Iterable[str] = (),
    recursive: bool = True,
) -> Set[str]:
    """
    Return a `set` of all distribution names which are required by the
    distribution specified in `requirement_string`.

    Parameters:

    - requirement_string (str): A distribution name, or a requirement string
      indicating both a distribution name and extras.
    - exclude ([str]): The name of one or more distributions to *exclude*
      from requirements lookup. Please note that excluding a distribution will
      also halt recursive lookup of requirements for that distribution.
    - recursive (bool): If `True` (the default), required distributions will
      be obtained recursively.
    """
    if isinstance(exclude, str):
        exclude = {normalize_name(exclude)}
    else:
        exclude = set(map(normalize_name, exclude))
    return set(
        _iter_requirement_names(
            _get_package_requirement(requirement_string),
            exclude=exclude,
            recursive=recursive,
        )
    )


def _get_pkg_requirement_name(requirement: pkg_resources.Requirement) -> str:
    return normalize_name(requirement.project_name)


def _iter_requirement_names(
    requirement: pkg_resources.Requirement,
    exclude: Set[str],
    recursive: bool = True,
) -> Iterable[str]:
    project_name: str = normalize_name(requirement.project_name)
    extras: Set[str] = set(map(normalize_name, requirement.extras))
    if project_name in exclude:
        return ()
    distribution: pkg_resources.Distribution = get_installed_distributions()[
        project_name
    ]
    requirements: List[pkg_resources.Requirement] = distribution.requires(
        extras=tuple(sorted(extras))
    )

    def iter_requirement_names_(
        requirement_: pkg_resources.Requirement,
    ) -> Iterable[str]:
        return _iter_requirement_names(
            requirement_, exclude=exclude, recursive=recursive
        )

    def not_excluded(name: str) -> bool:
        return name not in exclude

    requirement_names: Iterable[str] = filter(
        not_excluded, map(_get_pkg_requirement_name, requirements)
    )
    if recursive:
        requirement_names = chain(
            requirement_names, *map(iter_requirement_names_, requirements)
        )
    return requirement_names
