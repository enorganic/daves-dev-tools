import unittest
import os
import tomli
from typing import Iterable
from configparser import ConfigParser
from packaging.requirements import Requirement
from packaging.specifiers import Specifier
from packaging.version import Version
from daves_dev_tools.requirements.update import (
    get_updated_requirements_txt,
    get_updated_setup_cfg,
    get_updated_pyproject_toml,
)


TEST_PROJECT_DIRECTORY: str = os.path.join(
    os.path.dirname(__file__), "test_projects/test_project_a/"
)


def is_nonzero(value: int) -> bool:
    return isinstance(value, int) and value != 0


def is_zero(value: int) -> bool:
    return isinstance(value, int) and value == 0


def validate_nonzero_specifier(specifier: Specifier) -> None:
    # Ensure this release version is not 0, 0.0, 0.0.0, etc.
    assert any(map(is_nonzero, Version(specifier.version).release)), str(
        specifier
    )


def validate_zero_specifier(specifier: Specifier) -> None:
    # Ensure this release version is not 0, 0.0, 0.0.0, etc.
    assert all(map(is_zero, Version(specifier.version).release)), str(
        specifier
    )


def validate_requirement(requirement_string: str) -> None:
    print(requirement_string)
    if requirement_string:
        print(requirement_string)
        requirement: Requirement = Requirement(requirement_string)
        if requirement.name in ("pip", "setuptools"):
            list(
                map(
                    validate_zero_specifier,  # type: ignore
                    requirement.specifier,
                )
            )
        else:
            list(
                map(
                    validate_nonzero_specifier,  # type: ignore
                    requirement.specifier,
                )
            )


def validate_requirements(requirements: Iterable[str]) -> None:
    if isinstance(requirements, str):
        requirements = requirements.split("\n")
    list(map(validate_requirement, requirements))


class TestRequirementsUpdate(unittest.TestCase):
    """
    This test case validates functionality for
    `daves_dev_tools.requirements.update`
    """

    def test_get_updated_setup_cfg(self) -> None:
        """
        Ensure that updating a setup.cfg file occurs without problems
        """
        setup_cfg_path: str = os.path.join(TEST_PROJECT_DIRECTORY, "setup.cfg")
        updated_setup_cfg_data: str
        with open(setup_cfg_path) as setup_cfg_io:
            setup_cfg_data: str = setup_cfg_io.read()
            # Update versions for all packages *except* pip
            updated_setup_cfg_data = get_updated_setup_cfg(
                setup_cfg_data,
                ignore=("pip", "setuptools"),
                all_extra_name="all",
            )
            print(
                f"{setup_cfg_path.strip()}\n\n"
                "Before:\n\n"
                f"{setup_cfg_data.strip()}\n\n"
                "After:\n\n"
                f"{updated_setup_cfg_data.strip()}\n"
            )
            assert updated_setup_cfg_data != setup_cfg_data
        # Ensure all versions are updated to a non-zero release number
        parser: ConfigParser = ConfigParser()
        parser.read_string(updated_setup_cfg_data)
        validate_requirements(parser["options"]["install_requires"])
        extra_requirements_string: str
        for extra_requirements_string in parser[
            "options.extras_require"
        ].values():
            validate_requirements(extra_requirements_string)

    def test_get_updated_pyproject_toml(self) -> None:
        """
        Ensure that updating a pyproject.toml file occurs without problems
        """
        pyproject_toml_path: str = os.path.join(
            TEST_PROJECT_DIRECTORY, "pyproject.toml"
        )
        updated_pyproject_toml_data: str
        with open(pyproject_toml_path) as pyproject_toml_io:
            pyproject_toml_data: str = pyproject_toml_io.read()
            # Update versions for all packages *except* pip
            updated_pyproject_toml_data = get_updated_pyproject_toml(
                pyproject_toml_data,
                ignore=("pip", "setuptools"),
            )
            print(
                f"{pyproject_toml_path.strip()}\n\n"
                "Before:\n\n"
                f"{pyproject_toml_data.strip()}\n\n"
                "After:\n\n"
                f"{updated_pyproject_toml_data.strip()}\n"
            )
            assert updated_pyproject_toml_data != pyproject_toml_data
        # Ensure all versions are updated to a non-zero release number
        validate_requirements(
            tomli.loads(updated_pyproject_toml_data)["build-system"][
                "requires"
            ]
        )

    def test_get_updated_requirements_txt(self) -> None:
        """
        Ensure that updating a setup.cfg file occurs without problems
        """
        requirements_txt_path: str = os.path.join(
            TEST_PROJECT_DIRECTORY, "requirements.txt"
        )
        with open(requirements_txt_path) as requirements_txt_io:
            requirements_txt_data: str = requirements_txt_io.read()
            updated_requirements_txt_data: str = get_updated_requirements_txt(
                requirements_txt_data, ignore=("pip", "setuptools")
            )
            print(
                f"{requirements_txt_path.strip()}\n\n"
                "Before:\n\n"
                f"{requirements_txt_data.strip()}\n\n"
                "After:\n\n"
                f"{updated_requirements_txt_data.strip()}\n"
            )
            assert updated_requirements_txt_data != requirements_txt_data
            validate_requirements(updated_requirements_txt_data)


if __name__ == "__main__":
    unittest.main()
