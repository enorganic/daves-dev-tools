import functools
import importlib
import os
import re
import sys
from distutils.core import run_setup
from time import time
from types import ModuleType
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from .utilities import run, run_module_as_main

lru_cache: Callable[..., Any] = functools.lru_cache


def _list_dist(root: str, modified_at_or_after: float = 0.0) -> FrozenSet[str]:
    dist_root: str = os.path.join(root, "dist")
    dist_file: str
    dist_sub_directories: List[str]
    dist_files: Iterable[str]
    try:
        dist_root, dist_sub_directories, dist_files = next(
            iter(os.walk(dist_root))
        )
    except StopIteration:
        raise FileNotFoundError(
            f"No distributions could be found in {dist_root}"
        )
    dist_files = (
        os.path.join(dist_root, dist_file) for dist_file in dist_files
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


def _setup(root: str) -> FrozenSet[str]:
    start_time: float = time()
    current_directory: str = os.path.abspath(os.path.curdir)
    os.chdir(root)
    try:
        abs_setup: str = os.path.join(root, "setup.py")
        setup_args: List[str] = ["sdist", "bdist_wheel"]
        print(f'{sys.executable} {abs_setup} {" ".join(setup_args)}')
        run_setup(abs_setup, setup_args)
    finally:
        os.chdir(current_directory)
    return _list_dist(root, modified_at_or_after=start_time)


def _get_help() -> bool:
    """
    If `-h` or `--help` keyword arguments are provided,
    retrieve the repository credentials and store them in the "TWINE_USERNAME"
    and "TWINE_PASSWORD" environment variables.
    """
    if set(sys.argv) & {"-h", "--help", "-H", "--HELP"}:
        help_: str = run(f"{sys.executable} -m twine upload -h", echo=False)
        help_ = re.sub(
            r"\btwine upload\b( \[-h\])?",
            (
                "daves-dev-tools distribute\\1 "
                "[-cu CERBERUS_URL] [-cp CERBERUS_PATH]\n"
                "                   "
            ),
            help_,
        )
        help_ = (
            f"{help_.rstrip()}\n"
            "  -cu CERBERUS_URL, --cerberus-url CERBERUS_URL\n"
            "                        The base URL of a Cerberus REST API.\n"
            "                        See: https://swoo.sh/3DBW2Vb\n"
            "  -cp CERBERUS_PATH, --cerberus-path CERBERUS_PATH\n"
            "                        A Cerberus secure data path (including "
            "/key) wherein a\n"
            "                        password with which to authenticate can "
            "be found.\n"
            "                        If no USERNAME is provided, the last "
            "part of this path\n"
            "                        (the secure data path entry key) is "
            "inferred as your\n"
            "                        username. See: https://swoo.sh/3DBW2Vb\n"
        )
        print(help_)
        return True
    return False


def _get_credentials_from_cerberus() -> Tuple[Optional[str], Optional[str]]:
    """
    If `--cerberus-url` and `--cerberus-path` keyword arguments are provided,
    retrieve the repository credentials and store them in the "TWINE_USERNAME"
    and "TWINE_PASSWORD" environment variables.
    """
    username: Optional[str] = _argv_pop(
        sys.argv, "-u", _argv_pop(sys.argv, "--username")
    )
    password: Optional[str] = None
    cerberus_url: Optional[str] = _argv_pop(
        sys.argv, "--cerberus-url", None
    ) or _argv_pop(sys.argv, "-cu", None)
    cerberus_path: Optional[str] = _argv_pop(
        sys.argv, "--cerberus-path", None
    ) or _argv_pop(sys.argv, "-cp", None)
    if cerberus_url and cerberus_path:
        # Only import the Cerberus utility if/when the "--cerberus-url"
        # and "--cerberus-path" keyword arguments are provided, as the
        # "cerberus-python-client" and "boto3" libraries needed for this
        # are optional (only installed with the package extra
        # "daves-dev-tools[cerberus]")
        cerberus: ModuleType = importlib.import_module(
            ".cerberus",
            (
                os.path.split(os.path.dirname(__file__))[-1]
                if __name__ == "__main__"
                else ".".join(__name__.split(".")[:-1])
            ),
        )
        if not username:
            # If no username is provided, we assume the username has
            # been concatenated with the path, and extract it
            cerberus_path_list: List[str] = cerberus_path.split("/")
            username = cerberus_path_list.pop()
            cerberus_path = "/".join(cerberus_path_list)
        secrets: Union[Dict[str, str], str, None] = getattr(
            cerberus, "get_cerberus_secrets"
        )(cerberus_url, cerberus_path)
        if secrets is not None:
            assert isinstance(secrets, dict)
            password = secrets[username]
            sys.argv += ["--username", username]
            sys.argv += ["--password", password]
    return username, password


def _dist(root: str, distributions: FrozenSet[str], echo: bool = True) -> None:
    run_module_as_main(
        "twine",
        arguments=(["upload"] + sys.argv[1:] + list(sorted(distributions))),
        directory=root,
        echo=False,
    )


def _cleanup(root: str) -> None:
    current_directory: str = os.path.abspath(os.path.curdir)
    os.chdir(root)
    try:
        run_setup(os.path.join(root, "setup.py"), ["clean", "--all"])
    finally:
        os.chdir(current_directory)


def _negative_enumerate_index(item: Tuple[int, Any]) -> Tuple[int, Any]:
    return -item[0], item[1]


def _argv_get_last_index(
    argv: List[str], keys: Optional[Set[str]] = None
) -> Optional[int]:
    """
    Return the index of the last item in `argv` which matches one of the
    indicated keys, or `None`, if not found. If no keys are provided,
    find the index of the last positional argument.
    """
    if isinstance(keys, str):
        keys = {keys}
    index: int
    for index, value in map(
        _negative_enumerate_index, enumerate(reversed(argv), 1)  # type: ignore
    ):
        if keys is not None:
            if value in keys:
                return index
        elif not value.startswith("-"):
            try:
                if not argv[index - 1].startswith("-"):
                    return -index
            except IndexError:
                pass
    return None


def _argv_pop_last_positional(argv: List[str], default: str = "") -> str:
    index: Optional[int] = _argv_get_last_index(argv)
    if index is not None:
        return argv.pop(index)
    return default


def _argv_pop(
    argv: List[str], key: str, default: Optional[str] = None
) -> Optional[str]:
    key_index: int
    value: Optional[str] = default
    # Ensure we are looking for a keyword argument
    assert key.startswith("-")
    try:
        key_index = argv.index(key)
        # Ensure there is a value
        assert len(argv) > key_index + 1
        value = argv.pop(key_index + 1)
        argv.pop(key_index)
    except ValueError:
        pass
    return value


def main(root: str = "") -> None:
    if not _get_help():
        _get_credentials_from_cerberus()
        root = root or _argv_pop_last_positional(sys.argv, ".")
        root = os.path.abspath(root).rstrip("/")
        try:
            _dist(root, _setup(root))
        finally:
            _cleanup(root)


if __name__ == "__main__":
    main()
