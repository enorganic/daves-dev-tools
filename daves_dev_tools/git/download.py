import argparse
import os
from itertools import chain
from glob import glob
from pipes import quote
from shutil import rmtree
from typing import Iterable, List
from ..utilities import create_timestamped_temp_directory, run


def download(
    repo: str,
    files: Iterable[str] = ("**"),
    directory: str = "",
    branch: str = "",
    echo: bool = False,
) -> List[str]:
    """
    Download files from a git repository and return a list of the files
    downloaded.

    Parameters:

    - repo (str): A git URL, as you would pass to `git clone`
    - files ([str]): One or more "glob" patterns or relative file paths
    - directory (str): The target directory (if not provided, the current
      directory is used)
    - branch (str): A branch from which to retrieve (if not provided,
      files will be retrieved from HEAD)
    """
    if isinstance(files, str):
        files = (files,)
    if not directory:
        directory = os.path.curdir
    directory = os.path.abspath(directory)
    temp_directory: str = create_timestamped_temp_directory("git_download_")
    # Shallow clone into a temp directory
    command: str = (
        f"git clone {quote(repo)} {quote(temp_directory)} "
        "--depth 1 --single-branch "
    )
    if branch:
        command = f"{command} -b {quote(branch)}"
    run(command, echo=echo)
    # Remove the git directory, so those files aren't accidentally matched
    rmtree(os.path.join(temp_directory, ".git"))
    current_directory: str = os.path.abspath(os.path.curdir)
    path: str
    try:
        os.chdir(temp_directory)
        matched_files: Iterable[str] = map(
            lambda path: os.path.join(temp_directory, path),  # type: ignore
            chain(*map(glob, files)),  # type: ignore
        )
    finally:
        os.chdir(current_directory)
    downloaded_paths: List[str] = []
    new_path: str
    for path in matched_files:
        new_path = os.path.join(directory, os.path.basename(path))
        os.rename(path, new_path)
        downloaded_paths.append(new_path)
    rmtree(temp_directory)
    return downloaded_paths


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="daves-dev-tools git download",
        description=(
            "Download files from a git repository matching one or more "
            "specified file names or glob patterns"
        ),
    )
    parser.add_argument(
        "-b",
        "--branch",
        default="",
        type=str,
        help=("Retrieve files from BRANCH instead of the remote's HEAD"),
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="",
        type=str,
        help=(
            "The directory under which to save matched files. "
            "If not provided, files will be saved under the current "
            "directory."
        ),
    )
    parser.add_argument(
        "-e",
        "--echo",
        default=False,
        const=True,
        action="store_const",
        help="Print the downloaded file paths",
    )
    parser.add_argument("repo", type=str, help="Reference repository")
    parser.add_argument(
        "file",
        nargs="*",
        type=str,
        help=(
            "One or more `glob` pattern(s) indicating a specific file or "
            "files to include. If not provided, all files "
            "in the repository will be included."
        ),
    )
    arguments: argparse.Namespace = parser.parse_args()
    download(
        arguments.repo,
        files=arguments.files or ("**",),
        directory=arguments.directory,
        branch=arguments.branch,
    )


if __name__ == "__main__":
    main()
