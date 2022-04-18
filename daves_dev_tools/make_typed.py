import argparse
from collections import deque
import os
import re
from io import StringIO
from pathlib import Path
from typing import IO, Set
from typing import Tuple
from configparser import ConfigParser
from .requirements.utilities import (
    iter_distribution_location_file_paths,
)


def _get_project_and_setup_cfg_paths(path: str = ".") -> Tuple[str, str]:
    setup_cfg_path: str
    project_path: str
    if not os.path.isdir(path):
        assert os.path.basename(path).lower() == "setup.cfg"
        setup_cfg_path = path
        project_path = os.path.dirname(path)
    else:
        setup_cfg_path = os.path.join(path, "setup.cfg")
        project_path = path
    return project_path, setup_cfg_path


def _touch_packages_py_typed(project_path: str) -> None:
    py_typed_paths: Set[str] = set()
    setup_py_path: str = str(
        Path(project_path).absolute().joinpath("setup.py")
    )

    def touch_py_typed(path: str) -> None:
        if path.endswith(".py"):
            absolute_path: Path = Path(path).absolute()
            if str(absolute_path) != setup_py_path:
                py_typed_path: Path = absolute_path.parent.joinpath("py.typed")
                py_typed_path_str: str = str(py_typed_path)
                if py_typed_path_str not in py_typed_paths:
                    print(f"touch {py_typed_path}")
                    py_typed_path.touch()
                    py_typed_paths.add(py_typed_path_str)

    deque(
        map(
            touch_py_typed, iter_distribution_location_file_paths(project_path)
        ),
        maxlen=0,
    )


def _update_setup_cfg(
    setup_cfg_path: str,
) -> None:
    parser: ConfigParser = ConfigParser()
    if os.path.isfile(setup_cfg_path):
        parser.read(setup_cfg_path)
    if not parser.has_section("options"):
        parser.add_section("options")
    parser.set("options", "include_package_data", "True")
    if not parser.has_section("options.package_data"):
        parser.add_section("options.package_data")
    package_data: str = parser.get(
        "options.package_data", "*", fallback=""
    ).rstrip()
    if "py.typed" not in filter(  # type: ignore
        None,
        map(
            os.path.normpath,  # type: ignore
            map(str.strip, package_data.split("\n")),
        ),
    ):
        parser.set(
            "options.package_data",
            "*",
            "py.typed",
        )
    print(f"Writing {setup_cfg_path}")
    setup_cfg: str
    setup_cfg_io: IO[str]
    with StringIO() as setup_cfg_io:
        parser.write(setup_cfg_io)
        setup_cfg_io.seek(0)
        setup_cfg = re.sub(r"[ ]+(\n|$)", r"\1", setup_cfg_io.read()).strip()
        setup_cfg = f"{setup_cfg}\n"
    with open(setup_cfg_path, "w") as setup_cfg_io:
        setup_cfg_io.write(setup_cfg)


def make_typed(path: str = ".") -> None:
    """
    Create (if needed) **/py.typed files and alter the setup.cfg file such that
    a distribution's packages will be identified as being fully type-hinted
    """
    project_path: str
    setup_cfg_path: str
    project_path, setup_cfg_path = _get_project_and_setup_cfg_paths(path)
    # Create py.typed files
    _touch_packages_py_typed(project_path)
    # Parse and update setup.cfg
    _update_setup_cfg(setup_cfg_path)


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="daves-dev-tools make-typed",
        description=(
            "Add **/py.typed files and alter the setup.cfg such that a "
            "distribution's packages will be identifiable as fully type-hinted"
        ),
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        type=str,
        help=(
            "A project directory (where the setup.py and/or setup.cfg file "
            "are located)"
        ),
    )
    arguments: argparse.Namespace = parser.parse_args()
    make_typed(arguments.path)


if __name__ == "__main__":
    main()
