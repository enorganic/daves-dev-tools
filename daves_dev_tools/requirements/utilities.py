import sys
import os
import tomli
import pkg_resources
from warnings import warn
from pipes import quote
from configparser import ConfigParser, SectionProxy
from enum import Enum, auto
from itertools import chain
from typing import Dict, Iterable, Set, Tuple, List, IO, Union, Callable, Any
from packaging.utils import canonicalize_name
from packaging.requirements import InvalidRequirement, Requirement
from more_itertools import unique_everseen
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


class ConfigurationFileType(Enum):

    REQUIREMENTS_TXT = auto()
    SETUP_CFG = auto()
    TOX_INI = auto()
    PYPROJECT_TOML = auto()


@lru_cache()
def get_configuration_file_type(path: str) -> ConfigurationFileType:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    basename: str = os.path.basename(path).lower()
    if basename == "setup.cfg":
        return ConfigurationFileType.SETUP_CFG
    elif basename == "tox.ini":
        return ConfigurationFileType.TOX_INI
    elif basename == "pyproject.toml":
        return ConfigurationFileType.PYPROJECT_TOML
    elif basename.endswith(".txt"):
        return ConfigurationFileType.REQUIREMENTS_TXT
    else:
        raise ValueError(
            f"{path} is not a recognized type of configuration file."
        )


def is_configuration_file(path: str) -> bool:
    try:
        get_configuration_file_type(path)
    except (FileNotFoundError, ValueError):
        return False
    return True


def refresh_working_set() -> None:
    """
    Force a refresh of all distribution information and clear related caches
    """
    get_installed_distributions.cache_clear()
    is_editable.cache_clear()
    is_installed.cache_clear()
    get_requirement_string_distribution_name.cache_clear()
    pkg_resources.working_set.entries = []
    pkg_resources.working_set.__init__()  # type: ignore


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
def is_installed(distribution_name: str) -> bool:
    return normalize_name(distribution_name) in get_installed_distributions()


def get_requirement_distribution_name(requirement: Requirement) -> str:
    return normalize_name(requirement.name)


@lru_cache()
def get_requirement_string_distribution_name(requirement_string: str) -> str:
    return get_requirement_distribution_name(
        get_requirement(requirement_string)
    )


@lru_cache()
def is_requirement_string(requirement_string: str) -> bool:
    try:
        Requirement(requirement_string)
    except InvalidRequirement:
        return False
    return True


def _iter_file_requirement_strings(path: str) -> Iterable[str]:
    lines: List[str]
    requirement_file_io: IO[str]
    with open(path) as requirement_file_io:
        lines = requirement_file_io.readlines()
    return filter(is_requirement_string, lines)


def _iter_setup_cfg_requirement_strings(path: str) -> Iterable[str]:
    parser: ConfigParser = ConfigParser()
    parser.read(path)
    requirement_strings: Iterable[str] = ()
    if ("options" in parser) and ("install_requires" in parser["options"]):
        requirement_strings = chain(
            requirement_strings,
            filter(
                is_requirement_string,
                parser["options"]["install_requires"].split("\n"),
            ),
        )
    if "options.extras_require" in parser:
        extras_require: SectionProxy = parser["options.extras_require"]
        extra_requirements_string: str
        for extra_requirements_string in extras_require.values():
            requirement_strings = chain(
                requirement_strings,
                filter(
                    is_requirement_string,
                    extra_requirements_string.split("\n"),
                ),
            )
    return unique_everseen(requirement_strings)


def _iter_tox_ini_requirement_strings(path: str) -> Iterable[str]:
    parser: ConfigParser = ConfigParser()
    parser.read(path)

    def get_section_option_requirements(
        section_name: str, option_name: str
    ) -> Iterable[str]:
        if parser.has_option(section_name, option_name):
            return filter(
                is_requirement_string,
                parser.get(section_name, option_name).split("\n"),
            )
        return ()

    def get_section_requirements(section_name: str) -> Iterable[str]:
        requirements: Iterable[str] = get_section_option_requirements(
            section_name, "deps"
        )
        if section_name == "tox":
            requirements = chain(
                requirements,
                get_section_option_requirements(section_name, "requires"),
            )
        return requirements

    return unique_everseen(
        chain(("tox",), *map(get_section_requirements, parser.sections()))
    )


def _iter_pyproject_toml_requirement_strings(path: str) -> Iterable[str]:
    pyproject_io: IO[str]
    with open(path) as pyproject_io:
        pyproject: Dict[str, Any] = tomli.loads(pyproject_io.read())
        if ("build-system" in pyproject) and (
            "requires" in pyproject["build-system"]
        ):
            return pyproject["build-system"]["requires"]
    return ()


def iter_configuration_file_requirement_strings(path: str) -> Iterable[str]:
    """
    Read a configuration file and yield the parsed requirements.
    """
    configuration_file_type: ConfigurationFileType = (
        get_configuration_file_type(path)
    )
    if configuration_file_type == ConfigurationFileType.SETUP_CFG:
        return _iter_setup_cfg_requirement_strings(path)
    elif configuration_file_type == ConfigurationFileType.PYPROJECT_TOML:
        return _iter_pyproject_toml_requirement_strings(path)
    elif configuration_file_type == ConfigurationFileType.TOX_INI:
        return _iter_tox_ini_requirement_strings(path)
    else:
        assert (
            configuration_file_type == ConfigurationFileType.REQUIREMENTS_TXT
        )
        return _iter_file_requirement_strings(path)


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
    _reinstall_location(distribution.location, echo=echo)


def _reinstall_location(location: str, echo: bool = False) -> bool:
    try:
        run(
            (
                f"{quote(sys.executable)} -m pip install --no-deps "
                f"-e {quote(location)}"
            ),
            echo=echo,
        )
        _reinstalled_locations.add(os.path.abspath(location))
        return True
    except OSError:
        # If an error code is returned, we just assume package metadata is
        # up-to-date
        return False


def reinstall_location(location: str, echo: bool = False) -> str:
    """
    Re-install a distribution at the local file path `location`,
    and return the distribution name, or "" if no distribution could
    be found
    """
    if _reinstall_location(location, echo):
        return _get_location_distribution_name(location)
    return ""


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
    refresh_working_set()


def _get_setup_py_distribution_name(path: str) -> str:
    current_directory: str = os.curdir
    if os.path.basename(path).lower() == "setup.py":
        os.chdir(os.path.dirname(path))
    else:
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        os.chdir(path)
        path = os.path.join(path, "setup.py")
    try:
        name: str = (
            run(f"{quote(sys.executable)} {quote(path)} --name", echo=False)
            .strip()
            .split("\n")[-1]
        )
    except OSError:
        name = ""
    os.chdir(current_directory)
    return name


def _get_setup_cfg_distribution_name(path: str) -> str:
    if os.path.basename(path).lower() != "setup.cfg":
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        path = os.path.join(path, "setup.cfg")
    if os.path.isfile(path):
        parser: ConfigParser = ConfigParser()
        parser.read(path)
        if "metadata" in parser:
            return parser.get("metadata", "name", fallback="")
    return ""


def get_setup_distribution_name(path: str) -> str:
    """
    Get a distribution's name from setup.py or setup.cfg
    """
    return normalize_name(
        _get_setup_py_distribution_name(path)
        or _get_setup_cfg_distribution_name(path)
    )


def _setup_dist_egg_info(location: str) -> None:
    setup_py_path: str = os.path.join(location, "setup.py")
    # If there is no setup.py file, we can't update egg info
    if not os.path.isfile(setup_py_path):
        return
    current_directory: str = os.curdir
    os.chdir(location)
    try:
        run(
            (
                f"{quote(sys.executable)} {quote(setup_py_path)} -q "
                "dist_info egg_info"
            ),
            echo=False,
        )
    except OSError:
        pass
    os.chdir(current_directory)


def setup_dist_egg_info(directory: str) -> None:
    """
    Refresh dist-info and egg-info for the editable package installed in
    `directory`
    """
    directory = os.path.abspath(directory)
    if not os.path.isdir(directory):
        directory = os.path.dirname(directory)
    return _setup_dist_egg_info(directory)


def get_setup_distribution_requirements(
    path: str,
) -> Dict[str, Tuple[str, ...]]:
    """
    Get a distribution's name from setup.py or setup.cfg
    """
    return normalize_name(
        _get_setup_py_distribution_name(path)
        or _get_setup_cfg_distribution_name(path)
    )


def _get_location_distribution_name(location: str) -> str:
    """
    Get a distribution name based on an installation location, or return
    an empty string if no distribution can be found
    """
    _setup_dist_egg_info(location)
    location = os.path.abspath(location)

    def _is_in_location(
        name_distribution: Tuple[str, pkg_resources.Distribution]
    ) -> bool:
        return os.path.abspath(name_distribution[1].location) == location

    def _get_name(
        name_distribution: Tuple[str, pkg_resources.Distribution]
    ) -> str:
        return name_distribution[0]

    try:
        return next(
            map(
                _get_name,
                filter(_is_in_location, get_installed_distributions().items()),
            )
        )
    except StopIteration:
        return get_setup_distribution_name(location)


def _get_pkg_requirement(
    requirement_string: str,
) -> pkg_resources.Requirement:
    requirement: Union[
        Requirement, pkg_resources.Requirement
    ] = _get_requirement(requirement_string, pkg_resources.Requirement.parse)
    assert isinstance(requirement, pkg_resources.Requirement)
    return requirement


def get_requirement(
    requirement_string: str,
) -> Requirement:
    requirement: Union[
        Requirement, pkg_resources.Requirement
    ] = _get_requirement(requirement_string, Requirement)
    assert isinstance(requirement, Requirement)
    return requirement


def _get_requirement(
    requirement_string: str,
    constructor: Callable[
        [str], Union[Requirement, pkg_resources.Requirement]
    ],
) -> Union[Requirement, pkg_resources.Requirement]:
    try:
        return constructor(requirement_string)
    except (
        InvalidRequirement,
        getattr(
            pkg_resources, "extern"
        ).packaging.requirements.InvalidRequirement,
        getattr(pkg_resources, "RequirementParseError"),
    ):
        # Try to parse the requirement as an installation target location,
        # such as can be used with `pip install`
        location: str = requirement_string
        extras: str = ""
        if "[" in requirement_string and requirement_string.endswith("]"):
            parts: List[str] = requirement_string.split("[")
            location = "[".join(parts[:-1])
            extras = f"[{parts[-1]}"
        location = os.path.abspath(location)
        name: str = _get_location_distribution_name(location)
        assert name, f"No distribution found in {location}"
        return constructor(f"{name}{extras}")


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
            _get_pkg_requirement(requirement_string),
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
    name: str = normalize_name(requirement.project_name)
    extras: Set[str] = set(map(normalize_name, requirement.extras))
    if name in exclude:
        return ()
    distribution: pkg_resources.Distribution
    try:
        distribution = get_installed_distributions()[name]
    except KeyError:
        warn(
            'The distribution "{name}" was not installed, '
            "attempting to install it now..."
        )
        run(
            (
                f"{quote(sys.executable)} -m pip install "
                f"{quote(str(requirement))}"
            ),
            echo=True,
        )
        refresh_working_set()
        return _iter_requirement_names(requirement, exclude, recursive)
    # Ensure requirements are up-to-date
    if _distribution_is_editable(distribution):
        _setup_dist_egg_info(distribution.location)
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


def _iter_requirement_strings_required_distribution_names(
    requirement_strings: Iterable[str],
) -> Iterable[str]:
    visited_requirement_strings: Set[str] = set()
    if isinstance(requirement_strings, str):
        requirement_strings = (requirement_strings,)

    def get_required_distribution_names_(requirement_string: str) -> Set[str]:
        if requirement_string not in visited_requirement_strings:
            try:
                name: str = get_requirement_string_distribution_name(
                    requirement_string
                )
                visited_requirement_strings.add(requirement_string)
                return get_required_distribution_names(requirement_string) | {
                    name
                }
            except KeyError:
                pass
        return set()

    return unique_everseen(
        chain(*map(get_required_distribution_names_, requirement_strings)),
    )


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
                ),
            ),
            key=lambda name: name.lower(),
        )
    )
