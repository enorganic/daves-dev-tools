import argparse
import functools
import importlib
import os
import runpy
import sys
from distutils.core import run_setup
from shutil import rmtree
from types import ModuleType
from typing import (
    Any, Callable, Dict, FrozenSet, List, Optional, Set, Tuple, Union
)

lru_cache: Callable[..., Any] = functools.lru_cache


def _list_dist(root: str) -> FrozenSet[str]:
    try:
        return frozenset((
            f'dist/{file_name}'
            for file_name in os.listdir(os.path.join(root, 'dist'))
        ))
    except (NotADirectoryError, FileNotFoundError):
        return frozenset()


def _setup(root: str) -> FrozenSet[str]:
    existing_distributions: FrozenSet[str] = _list_dist(root)
    current_directory: str = os.path.curdir
    os.chdir(root)
    try:
        run_setup('setup.py', ['sdist', 'bdist_wheel'])
    finally:
        os.chdir(current_directory)
    return _list_dist(root) - existing_distributions


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
            sys.argv += ['-u', username]
            # os.environ['TWINE_USERNAME'] = username
            sys.argv += ['-p', password]
            # os.environ['TWINE_PASSWORD'] = password
    return username, password


def _dist(root: str, distributions: FrozenSet[str]) -> None:
    argv: List[str] = sys.argv
    twine_argv: List[str] = (
        [None, 'upload'] + sys.argv[1:] + (
            list(sorted(distributions))
            if distributions else
            [f'dist/*']
        )
    )
    current_directory: str = os.path.curdir
    os.chdir(root)
    try:
        sys.argv = twine_argv
        print(' '.join(['twine'] + twine_argv[1:]))
        runpy.run_module('twine', run_name='__main__')
    finally:
        os.chdir(current_directory)
        sys.argv = argv


def _cleanup(root: str) -> None:
    current_directory: str = os.path.curdir
    os.chdir(root)
    try:
        run_setup('setup.py', ['clean', '--all'])
    finally:
        os.chdir(current_directory)


def _argv_remove(argv: List[str], key: str) -> int:
    index: int = -1
    try:
        index = argv.index(key)
        argv.pop(index)
    except ValueError:
        pass
    return index


def _argv_pop(argv: List[str], key: str, default: Optional[str] = None) -> str:
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
    assert _argv_remove(sys.argv, root) >= 0
    _get_credentials_from_cerberus()
    root = os.path.abspath(root).rstrip("/")
    try:
        new_distributions: FrozenSet[str] = _setup(root)
        try:
            _dist(root, new_distributions)
        except:  # noqa
            distribution: str
            for distribution in new_distributions:
                os.remove(distribution)
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
        default=".",
        help='The root directory path for the project.'
    )
    arguments: argparse.Namespace = parser.parse_known_args()[0]
    main(arguments.root)

