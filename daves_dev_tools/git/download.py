import argparse


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="daves-dev-tools git download"
    )
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
    assert parser
    raise NotImplementedError()


if __name__ == "__main__":
    main()
