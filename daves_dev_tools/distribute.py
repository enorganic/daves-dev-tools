import argparse
import os
import runpy
import sys
from distutils.core import run_setup
from typing import List


def _setup(root: str) -> None:
    current_directory: str = os.path.curdir
    os.chdir(root)
    try:
        run_setup('setup.py', ['sdist', 'bdist_wheel'])
    finally:
        os.chdir(current_directory)


def _dist(root: str) -> None:
    argv: List[str] = sys.argv
    current_directory: str = os.path.curdir
    os.chdir(root)
    try:
        sys.argv = [None, 'upload'] + sys.argv[1:] + [f'dist/*']
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


def main(root: str) -> None:
    sys.argv.remove(root)
    root = os.path.abspath(root).rstrip("/")
    try:
        _setup(root)
        _dist(root)
    finally:
        _cleanup(root)


if __name__ == '__main__':
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='Parse command-line arguments for a "distribute" operation'
    )
    parser.add_argument(
        "root",
        default=".",
        help='The root directory path for the project.'
    )
    arguments: argparse.Namespace = parser.parse_known_args()[0]
    main(arguments.root)

