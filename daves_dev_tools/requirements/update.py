from io import StringIO
from dataclasses import dataclass
from pkg_resources import (
    Distribution, LegacyVersion, working_set, safe_name
)
from configparser import ConfigParser
from typing import Dict, Iterable, IO, List, Callable, Set, Union, Tuple, Any
from packaging.utils import canonicalize_name
from packaging.specifiers import Specifier, SpecifierSet
from packaging.requirements import Requirement
from packaging.version import Version, parse as parse_version
from ..utilities import lru_cache


@lru_cache()
def _normalize_name(name: str) -> str:
    """
    Normalize a project/distribution name
    """
    return safe_name(canonicalize_name(name)).lower()


@lru_cache()
def _get_installed_distributions() -> Dict[str, Distribution]:
    installed: Dict[str, Distribution] = {}
    for distribution in working_set:
        installed[_normalize_name(distribution.project_name)] = distribution
    return installed


def get_distribution(name: str) -> Distribution:
    return _get_installed_distributions()[_normalize_name(name)]


def update(path: str, ignore: Iterable[str] = ()) -> None:
    """
    Update the requirement versions in the specified file.

    Parameters:

    - path (str): A local file path
    - ignore ([str]): One or more project names to ignore
    """
    data: str
    update_function: Callable[[str], str]
    if path.endswith(".cfg"):
        update_function = get_updated_setup_cfg
    elif path.endswith(".txt"):
        update_function = get_updated_requirements_txt
    else:
        raise ValueError(
            f"Unrecognized file name extension: {path}\n"
            "Only configuration files or requirements files can be parsed "
            "(setup.cfg or *.txt)"
        )
    file_io: IO[str]
    with open(path) as file_io:
        data = file_io.read()
    updated_data: str = update_function(data, ignore)
    if updated_data == data:
        print(f"All requirements were already up-to-date in {path}")
    else:
        print(f"Updating requirements in {path}")
        with open(path, "w") as file_io:
            file_io.write(updated_data)


def get_updated_requirement_string(
    requirement_string: str,
    ignore: Set[str]
) -> str:
    """
    This function accepts a requirement string, and returns a requirement
    string updated to reflect the version of the requirement installed
    in the current environment
    """
    return _get_updated_requirement_string(
        requirement_string,
        set(map(
            _normalize_name,
            ignore
        ))
    )


@dataclass
class _Version:
    """
    Instances of this class can be be passed as `self` in a call
    to `packaging.version.Version.__str__`, and thereby can facilitate
    operations to mimic mutability for the aforementioned class.
    """

    epoch: int
    release: Tuple[int, ...]
    pre: Any
    post: Any
    dev: Any
    local: Any


def _update_requirement_specifiers(
    requirement: Requirement,
    installed_version_string: str
) -> None:
    """
    This function updates specifier version numbers for a requirement
    to match the installed version of the package
    """
    installed_version: Union[Version, LegacyVersion] = parse_version(
        installed_version_string
    )
    specifier: Specifier
    updated_specifier_strings: List[str] = []
    for specifier in requirement.specifier:  # type: ignore
        # Only update requirement to match our installed version
        # if the requirement is *inclusive*
        if "=" in specifier.operator:
            specifier_version: Union[Version, LegacyVersion] = parse_version(
                specifier.version
            )
            specifier_version_data: _Version = _Version(
                epoch=specifier_version.epoch,
                # Truncate the updated version requirement at the same
                # level of specificity as the old
                release=installed_version.release[
                    :len(specifier_version.release)
                ],
                pre=specifier_version.pre,
                post=specifier_version.post,
                dev=specifier_version.dev,
                local=specifier_version.local,
            )
            updated_specifier_strings.append(
                Version.__str__(specifier_version_data)  # type: ignore
            )
        else:
            updated_specifier_strings.append(str(specifier))
    requirement.specifier = SpecifierSet(",".join(updated_specifier_strings))


def _get_updated_requirement_string(
    requirement_string: str,
    ignore: Set[str]
) -> str:
    """
    This function updates version numbers in a requirement string to match
    those installed in the current environment
    """
    requirement: Requirement = Requirement(requirement_string)
    name: str = _normalize_name(requirement.name)
    if name in ignore:
        return requirement_string
    distribution: Distribution = _get_installed_distributions()[
        name
    ]
    _update_requirement_specifiers(requirement, distribution.version)
    return str(requirement)


def get_updated_requirements_txt(data: str, ignore: Iterable[str] = ()) -> str:
    """
    Return the contents of a **requirements.txt** file, updated to reflect the
    currently installed project versions, excluding those specified in
    `ignore`.

    Parameters:

    - data (str): The contents of a **setup.cfg** file
    - ignore ([str]): One or more project names to leave as-is
    """
    return ""


def get_updated_setup_cfg(data: str, ignore: Iterable[str] = ()) -> str:
    """
    Return the contents of a **setup.cfg** file, updated to reflect the
    currently installed project versions, excluding those specified in
    `ignore`.

    Parameters:

    - data (str): The contents of a **setup.cfg** file
    - ignore ([str]): One or more project names to leave as-is
    """
    ignore_set: Set[str]
    # Normalize/harmonize excluded project names
    if isinstance(ignore, str):
        ignore_set = {ignore}
    else:
        ignore_set = set(map(_normalize_name, ignore))

    def get_updated_requirement(requirement: str) -> str:
        return _get_updated_requirement_string(requirement, ignore=ignore_set)

    # Parse
    parser: ConfigParser = ConfigParser()
    parser.read_string(data)
    # Update
    parser["options"]["install_requires"] = list(map(  # type: ignore
        get_updated_requirement,
        parser["options"]["install_requires"]
    ))
    extras_require: Dict[
        str, List[str]
    ] = parser["options.extras_require"]  # type: ignore
    extra_name: str
    extra_requirements: List[str]
    for extra_name, extra_requirements in extras_require.items():
        extras_require[extra_name] = list(map(
            get_updated_requirement,
            extra_requirements
        ))
    # Return as a string
    setup_cfg_io: IO[str]
    with StringIO() as setup_cfg_io:
        parser.write(setup_cfg_io)
    return setup_cfg_io.read()
