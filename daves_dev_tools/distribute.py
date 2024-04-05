import functools
import os
import re
import sys
import tempfile
from subprocess import check_output
from time import time
from typing import Any, Callable, FrozenSet, Iterable, List, Tuple

from setuptools import build_meta  # type: ignore

from .utilities import run_module_as_main, sys_argv_pop

lru_cache: Callable[..., Any] = functools.lru_cache
_SYS_ARGV: Tuple[str, ...] = tuple(sys.argv)


def _list_modified(
    directory: str, modified_at_or_after: float = 0.0
) -> FrozenSet[str]:
    dist_file: str
    dist_sub_directories: List[str]
    dist_files: Iterable[str]
    try:
        directory, dist_sub_directories, dist_files = next(
            iter(os.walk(directory))
        )
    except StopIteration:
        raise FileNotFoundError(
            f"No distributions could be found in {directory}"
        )
    dist_files = tuple(
        os.path.join(directory, dist_file) for dist_file in dist_files
    )
    if modified_at_or_after:
        dist_files = filter(
            lambda dist_file: (  # noqa
                os.path.getmtime(dist_file) >= modified_at_or_after
            ),
            dist_files,
        )
    try:
        return frozenset(dist_files)
    except (NotADirectoryError, FileNotFoundError):
        return frozenset()


def _setup(directory: str) -> FrozenSet[str]:
    start_time: float = time()
    current_directory: str = os.path.abspath(os.path.curdir)
    os.chdir(directory)
    try:
        metadata_directory: str = tempfile.mkdtemp()
        dist_directory: str = tempfile.mkdtemp()
        build_meta.build_sdist(dist_directory)
        build_meta.prepare_metadata_for_build_wheel(metadata_directory)
        build_meta.build_wheel(
            dist_directory, metadata_directory=metadata_directory
        )
    finally:
        os.chdir(current_directory)
    return _list_modified(dist_directory, modified_at_or_after=start_time)


def _get_help() -> bool:
    """
    If `-h` or `--help` keyword arguments are provided,
    retrieve the repository credentials and store them in the "TWINE_USERNAME"
    and "TWINE_PASSWORD" environment variables.
    """
    if set(_SYS_ARGV) & {"-h", "--help", "-H", "--HELP"}:
        help_: str = check_output(
            (sys.executable, "-m", "twine", "upload", "-h"),
            encoding="utf-8",
            universal_newlines=True,
        ).strip()
        help_ = re.sub(
            r"\btwine upload\b",
            "daves-dev-tools distribute",
            help_,
        )
        help_ = re.sub(
            (
                r"(\n\s*)dist \[dist \.\.\.\](?:.|\n)+"
                r"(\npositional arguments:\s*\n\s*)(?:.|\n)+"
                r"(\noptional arguments:\s*\n)"
            ),
            (
                r"\1[directory]"
                r"\n\2directory             "
                "The root directory path for the project."
                r"\n\3"
            ),
            help_,
        )
        print(help_)
        return True
    return False


def _dist(
    directory: str, distributions: FrozenSet[str], echo: bool = True
) -> None:
    arguments: Tuple[str, ...] = (
        ("upload",) + tuple(_SYS_ARGV[1:]) + tuple(sorted(distributions))
    )
    run_module_as_main(
        "twine",
        arguments=arguments,
        directory=directory,
        echo=False,
    )


def main() -> None:
    if not _get_help():
        directory: str = sys_argv_pop(depth=2, default=".")  # type: ignore
        directory = os.path.abspath(directory).rstrip("/")
        _dist(directory, _setup(directory))


if __name__ == "__main__":
    main()
