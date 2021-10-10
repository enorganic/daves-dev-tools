import unittest
from subprocess import getstatusoutput
from typing import Union, Dict, Optional
from itertools import starmap
from daves_dev_tools.requirements.update import update


class TestRequirements(unittest.TestCase):
    """
    This test case validates functionality for the
    `daves_dev_tools.requirements` package.
    """

    def test_update(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main()
