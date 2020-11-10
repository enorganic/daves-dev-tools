import argparse
import functools
import importlib
import os
import runpy
import sys
from distutils.core import run_setup
from itertools import chain
from time import time
from types import ModuleType
from typing import (
    Any, Callable, Dict, FrozenSet, Iterable, List, Optional, Tuple, Union
)

lru_cache: Callable[..., Any] = functools.lru_cache


def _list_dist(
    root: str, modified_at_or_after: float = 0.0
) -> FrozenSet[str]:
    dist_file: str
    dist_root: str
    dist_sub_directories: List[str]
    dist_files: Iterable[str]
    dist_root, dist_sub_directories, dist_files = next(iter(
        os.walk(os.path.join(root, 'dist'))
    ))
    dist_files = (
        os.path.join(dist_root, dist_file)
        for dist_file in dist_files
    )
    if modified_at_or_after:
        dist_files = filter(
            lambda dist_file: (  # noqa
                os.path.getmtime(dist_file) >= modified_at_or_after
            ),
            dist_files
        )
    try:
        return frozenset(dist_files)
    except (NotADirectoryError, FileNotFoundError):
        return frozenset()


def _setup(root: str) -> FrozenSet[str]:
    start_time: float = time()
    current_directory: str = os.path.curdir
    os.chdir(root)
    try:
        run_setup(os.path.join(root, 'setup.py'), ['sdist', 'bdist_wheel'])
    finally:
        os.chdir(current_directory)
    return _list_dist(root, modified_at_or_after=start_time)


@lru_cache()
def _get_credentials_from_cerberus() -> Tuple[Optional[str], Optional[str]]:
    """
    If `--cerberus-url` and `--cerberus-path` keyword arguments are provided,
    retrieve the repository credentials and store them in the "TWINE_USERNAME"
    and "TWINE_PASSWORD" environment variables.
    """
    username: Optional[str] = _argv_pop(
        sys.argv, '-u', _argv_pop(sys.argv, '--username')
    )
    password: Optional[str] = None
    cerberus_url: Optional[str] = _argv_pop(sys.argv, '--cerberus-url')
    cerberus_path: Optional[str] = _argv_pop(sys.argv, '--cerberus-path')
    if cerberus_url and cerberus_path:
        # Only import the Cerberus utility if/when the "--cerberus-url"
        # and "--cerberus-path" keyword arguments are provided, as the
        # "cerberus-python-client" and "boto3" libraries needed for this
        # are optional (only installed with the package extra
        # "daves-dev-tools[cerberus]")
        cerberus: ModuleType = importlib.import_module(
            ".utilities.cerberus",
            (
                os.path.split(os.path.dirname(__file__))[-1]
                if __name__ == '__main__' else
                ".".join(__name__.split(".")[:-1])
            )
        )
        if not username:
            # If no username is provided, we assume the username has
            # been concatenated with the path, and extract it
            cerberus_path_list: List[str] = cerberus_path.split('/')
            username = cerberus_path_list.pop()
            cerberus_path = '/'.join(cerberus_path_list)
        secrets: Union[Dict[str, str], str, None] = getattr(
            cerberus, "get_cerberus_secrets"
        )(
            cerberus_url, cerberus_path
        )
        if secrets is not None:
            assert isinstance(secrets, dict)
            password = secrets[username]
            sys.argv += ['--username', username]
            sys.argv += ['--password', password]
    return username, password


def _dist(root: str, distributions: FrozenSet[str]) -> None:
    argv: List[str] = sys.argv
    twine_argv: List[str] = list(chain(
        sys.argv[:1],
        ['upload'],
        sys.argv[1:],
        sorted(distributions)
    ))
    current_directory: str = os.path.curdir
    os.chdir(root)
    print(' '.join(['twine'] + twine_argv[1:]))  # type: ignore
    try:
        sys.argv = twine_argv
        runpy.run_module('twine', run_name='__main__')
    finally:
        os.chdir(current_directory)
        sys.argv = argv


def _cleanup(root: str) -> None:
    current_directory: str = os.path.curdir
    os.chdir(root)
    try:
        run_setup(os.path.join(root, 'setup.py'), ['clean', '--all'])
    finally:
        os.chdir(current_directory)


def _argv_positional_last_index(argv: List[str], key: str) -> Optional[int]:
    index: int
    for index in range(len(argv) - 1, 0, -1):
        if argv[index] == key and not argv[index - 1].startswith('-'):
            return index
    return None


def _argv_remove_last_positional(argv: List[str], key: str) -> None:
    index: Optional[int] = _argv_positional_last_index(argv, key)
    if index is not None:
        argv.pop(index)


def _argv_pop(
    argv: List[str], key: str, default: Optional[str] = None
) -> Optional[str]:
    key_index: int
    value: Optional[str] = default
    # Ensure we are looking for a keyword argument
    assert key.startswith('-')
    try:
        key_index = argv.index(key)
        # Ensure there is a value
        assert len(argv) > key_index + 1
        value = argv.pop(key_index + 1)
        argv.pop(key_index)
    except ValueError:
        pass
    return value


def main(root: str) -> None:
    _argv_remove_last_positional(sys.argv, root)
    _get_credentials_from_cerberus()
    root = os.path.abspath(root).rstrip("/")
    try:
        _dist(root, _setup(root))
    finally:
        _cleanup(root)


if __name__ == '__main__':
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='Parse command-line arguments for a "distribute" operation'
    )
    parser.add_argument(
        "--cerberus-url",
        "-cu",
        type=str,
        default=None,
        help=(
            "The URL for a Cerberus API from which to retrieve repository "
            "credentials"
        )
    )
    parser.add_argument(
        "--cerberus-path",
        "-cp",
        type=str,
        default=None,
        help=(
            "The Cerberus path where repository credentials can be found"
        )
    )
    parser.add_argument(
        "root",
        type=str,
        default=".",
        nargs="?",
        help='The root directory path for the project.'
    )
    arguments: argparse.Namespace = parser.parse_known_args()[0]
    main(arguments.root)
