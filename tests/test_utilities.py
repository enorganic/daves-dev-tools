import unittest

from daves_dev_tools.utilities import update_url_user_password


class TestUtilities(unittest.TestCase):
    """
    This test case validates functionality for
    `daves_dev_tools.utilities`
    """

    def test_update_url_user_password(self) -> None:
        """
        Ensure that updating a setup.cfg file occurs without problems
        """
        assert (
            update_url_user_password(
                "https://host.com/path/file.ext?x=y#nowhere", "beetle", "juice"
            )
            == "https://beetle:juice@host.com/path/file.ext?x=y#nowhere"
        )


if __name__ == "__main__":
    unittest.main()
