import sys
import os
import pipes
from pkg_resources import Distribution, working_set, safe_name
from typing import Dict, Iterable, Set, Tuple
from packaging.utils import canonicalize_name
from packaging.requirements import InvalidRequirement, Requirement
from ..utilities import lru_cache, run


@lru_cache()
def normalize_name(name: str) -> str:
    """
    Normalize a project/distribution name
    """
    return safe_name(canonicalize_name(name)).lower()


@lru_cache()
def _get_installed_distributions() -> Dict[str, Distribution]:
    installed: Dict[str, Distribution] = {}
    for distribution in working_set:
        installed[normalize_name(distribution.project_name)] = distribution
    return installed


def get_distribution(name: str) -> Distribution:
    return _get_installed_distributions()[normalize_name(name)]


@lru_cache()
def is_requirement_string(requirement_string: str) -> bool:
    try:
        Requirement(requirement_string)
    except InvalidRequirement:
        return False
    return True


@lru_cache()
def is_editable(distribution_name: str) -> bool:
    """
    Return `True` if the indicated distribution is an editable installation.
    """
    return _distribution_is_editable(get_distribution(distribution_name))


def _distribution_is_editable(distribution: Distribution) -> bool:
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
    include_paths: Set[str],
    exclude_paths: Set[str],
) -> Iterable[Distribution]:
    def include_distribution_item(
        name_distribution: Tuple[str, Distribution]
    ) -> bool:
        name: str
        distribution: Distribution
        name, distribution = name_distribution
        if (
            ((not include) or (name in include))
            and ((not exclude) or (name not in exclude))
            and (
                (not include_paths)
                or (
                    os.path.abspath(distribution.location) not in include_paths
                )
            )
            and (
                (not exclude_paths)
                or (
                    os.path.abspath(distribution.location) not in exclude_paths
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
                _get_installed_distributions().items(),
            ),
        ),
    )


def _reinstall_distribution(
    distribution: Distribution, echo: bool = False
) -> None:
    run(
        (
            f"{pipes.quote(sys.executable)} -m pip install --no-deps "
            f"-e {pipes.quote(distribution.location)}"
        ),
        echo=echo,
    )


def reinstall_editable(
    include: Iterable[str] = (),
    exclude: Iterable[str] = (),
    include_paths: Iterable[str] = (),
    exclude_paths: Iterable[str] = (),
    echo: bool = False,
) -> None:
    """
    This function re-installs editable distributions.

    Parameters:

    - include ([str]):
      One or more distribution names to include (excluding all others)
    - exclude ([str])
      One or more distribution names to exclude
    - include_paths ([str])
      One or more distribution locations to include (excluding all others)
    - exclude_paths ([str])
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
    if isinstance(include_paths, str):
        include_paths = {os.path.abspath(include_paths)}
    else:
        include_paths = set(map(os.path.abspath, include_paths))
    if isinstance(exclude_paths, str):
        exclude_paths = {os.path.abspath(exclude_paths)}
    else:
        exclude_paths = set(map(os.path.abspath, exclude_paths))

    def reinstall_distribution_(distribution: Distribution) -> None:
        _reinstall_distribution(distribution, echo=echo)

    list(
        map(
            reinstall_distribution_,
            _iter_editable_distributions(
                include, exclude, include_paths, exclude_paths
            ),
        )
    )
    _get_installed_distributions.cache_clear()
