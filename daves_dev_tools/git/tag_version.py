import argparse
import os
from typing import Iterable
from subprocess import check_output, check_call
from ..requirements.utilities import get_setup_distribution_version


def tag_version(directory: str = os.path.curdir, message: str = "") -> None:
    """
    Tag your project with the package version number *if* no pre-existing
    tag with that version number exists.

    Parameters:

    - directory (str)
    - message (str)
    """
    version: str = get_setup_distribution_version(directory)
    if version:
        current_directory: str = os.path.abspath(os.path.curdir)
        os.chdir(directory)
        try:
            tags: Iterable[str] = map(
                str.strip,
                check_output(
                    ("git", "tag"), encoding="utf-8", universal_newlines=True
                )
                .strip()
                .split("\n"),
            )
            if version not in tags:
                check_call(
                    ("git", "tag", "-a", version, "-m", message or version)
                )
        finally:
            os.chdir(current_directory)


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="daves-dev-tools git tag-version",
        description=(
            "Tag your repo with the python package version, if a tag "
            "for that version doesn't already exist."
        ),
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=os.path.curdir,
        type=str,
        help=(
            "Your project directory. If not provided, the current "
            "directory will be used."
        ),
    )
    parser.add_argument(
        "-m",
        "--message",
        default="",
        type=str,
        help=(
            "The tag message. If not provided, the new version number is "
            "used."
        ),
    )
    arguments: argparse.Namespace = parser.parse_args()
    tag_version(directory=arguments.directory, message=arguments.message)


if __name__ == "__main__":
    main()
