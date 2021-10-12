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
    distribution_names: Set[str],
) -> Iterable[Distribution]:
    def include_distribution_item(
        name_distribution: Tuple[str, Distribution]
    ) -> bool:
        name: str
        distribution: Distribution
        name, distribution = name_distribution
        if (not distribution_names) or (name in distribution_names):
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
    distribution_names: Iterable[str] = (), echo: bool = False
) -> None:
    """
    This function re-installs editable distributions.
    """
    if isinstance(distribution_names, str):
        distribution_names = {normalize_name(distribution_names)}
    else:
        distribution_names = set(map(normalize_name, distribution_names))

    def reinstall_distribution_(distribution: Distribution) -> None:
        _reinstall_distribution(distribution, echo=echo)

    list(
        map(
            reinstall_distribution_,
            _iter_editable_distributions(distribution_names),
        )
    )
    _get_installed_distributions.cache_clear()
