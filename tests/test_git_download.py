import unittest
import os
from shutil import rmtree
from daves_dev_tools.utilities import run, create_timestamped_temp_directory
from daves_dev_tools.git.download import download


PROJECT_DIRECTORY: str = os.path.join(
    os.path.dirname(os.path.dirname(__file__))
)


class TestGitDownload(unittest.TestCase):
    """
    This test case validates functionality for
    `daves_dev_tools.git.download`
    """

    def test_git_download(self) -> None:
        temp_directory: str = create_timestamped_temp_directory(
            "test_git_download_"
        )
        current_directory: str = os.path.abspath(os.path.curdir)
        os.chdir(PROJECT_DIRECTORY)
        try:
            # Use this project's repo to test the download command
            origin: str = run("git remote get-url origin", echo=False)
            path: str
            for path in download(
                origin, files="**/*.py", directory=temp_directory
            ):
                assert path.endswith(".py")
        finally:
            os.chdir(current_directory)
            rmtree(temp_directory)


if __name__ == "__main__":
    # unittest.main()
    TestGitDownload().test_git_download()
