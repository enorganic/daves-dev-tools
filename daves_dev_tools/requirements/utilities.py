"""
This module now simply wraps `dependence.utilities`
(for backwards compatibility)
"""

from typing import List

from dependence.utilities import ConfigurationFileType
from dependence.utilities import cache_clear as refresh_working_set
from dependence.utilities import (
    get_configuration_file_type,
    get_distribution,
    get_editable_distribution_location,
    get_editable_distributions_locations,
    get_installed_distributions,
    get_required_distribution_names,
    get_requirement_distribution_name,
    get_requirement_string_distribution_name,
    get_requirements_required_distribution_names,
    get_setup_distribution_name,
    get_setup_distribution_version,
    install_requirement,
    is_configuration_file,
    is_editable,
    is_installed,
    is_requirement_string,
    iter_configuration_file_requirement_strings,
    iter_distribution_location_file_paths,
    normalize_name,
    refresh_editable_distributions,
    setup_dist_egg_info,
    setup_dist_info,
    setup_egg_info,
)

__all__: List[str] = [
    "is_configuration_file",
    "get_configuration_file_type",
    "get_distribution",
    "get_editable_distributions_locations",
    "refresh_working_set",
    "normalize_name",
    "ConfigurationFileType",
    "refresh_editable_distributions",
    "get_installed_distributions",
    "is_installed",
    "get_requirement_distribution_name",
    "get_requirement_string_distribution_name",
    "iter_configuration_file_requirement_strings",
    "is_requirement_string",
    "is_editable",
    "get_setup_distribution_name",
    "get_setup_distribution_version",
    "setup_dist_egg_info",
    "get_editable_distribution_location",
    "setup_dist_info",
    "setup_egg_info",
    "get_required_distribution_names",
    "install_requirement",
    "get_requirements_required_distribution_names",
    "iter_distribution_location_file_paths",
]
