"""
This module now simply wraps `dependence.freeze` (for backwards compatibility)
"""

from dependence.update import (
    get_updated_pyproject_toml,
    get_updated_requirements_txt,
    get_updated_setup_cfg,
    get_updated_tox_ini,
    main,
    update,
)

__all__ = [
    "main",
    "update",
    "get_updated_tox_ini",
    "get_updated_setup_cfg",
    "get_updated_requirements_txt",
    "get_updated_pyproject_toml",
]

if __name__ == "__main__":
    main()
