import os
from pathlib import Path
import sys
from typing import Tuple
import unittest
from daves_dev_tools.requirements.utilities import url2path


class TestRequirementsUtilities(unittest.TestCase):
    """
    This test case validates functionality for
    `daves_dev_tools.requirements.utilities`
    """

    def test_url2path(self) -> None:
        paths: Tuple[str, ...]
        if sys.platform == "win32":
            paths = (
                r"C:\directory\sub-directory\file-name.ext",
                r"C:\directory\sub directory\file name.ext",
                r"\\network-drive\directory\sub-directory\file-name.ext",
                r"\\network drive\directory\sub directory\file name.ext",
                r"\\network%20drive\directory\sub%20directory\file%20name.ext",
                # r"\\localhost\c$\WINDOWS\file.ext",
            )
        else:
            paths = (
                os.path.expanduser("~/directory/sub directory/file name.ext"),
                os.path.expanduser("~/directory/sub-directory/file-name.ext"),
                os.path.expanduser(
                    "~/directory/sub%20directory/file%20name.ext"
                ),
                os.path.expanduser("~/directory/sub-directory/file-name.ext"),
            )
        path: Path
        for path in map(Path, paths):
            assert str(url2path(path.as_uri())) == str(path)


if __name__ == "__main__":
    # unittest.main()
    TestRequirementsUtilities().test_url2path()
