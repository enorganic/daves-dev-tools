from functools import lru_cache
from typing import Any, Dict

import tomli


@lru_cache()
def pyproject_toml_defines_project(pyproject_toml_path: str) -> bool:
    pyproject: Dict[str, Any]
    try:
        with open(pyproject_toml_path, "r") as pyproject_io:
            pyproject = tomli.loads(pyproject_io.read())
    except FileNotFoundError:
        return False
    return bool(pyproject.get("project", {}).get("name"))
