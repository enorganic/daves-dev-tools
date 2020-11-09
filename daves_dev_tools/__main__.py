import argparse
import functools
import importlib
import runpy
import sys
from typing import Any, Callable

lru_cache: Callable[..., Any] = functools.lru_cache
_PACKAGE_NAME: str = __file__.split('/')[-2]


def main(operation: str) -> None:
    """
    Run a sub-module corresponding to the indicated `operation`.

    Parameters:

    - operation (str): The name of a sub-module to run as "__main__".
    """
    # Verify that a sub-module corresponding to the operation exists
    # importlib.import_module(f'.{operation}', _PACKAGE_NAME)
    sys.argv.remove(operation)
    module_name: str = f'{_PACKAGE_NAME}.{operation}'
    runpy.run_module(
        module_name,
        run_name='__main__'
    )


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Parse command-line arguments"
    )
    parser.add_argument(
        "operation",
        help='The name of a tool/operation (clean, distribute, etc.)?'
    )
    arguments: argparse.Namespace = parser.parse_known_args()[0]
    main(arguments.operation)
