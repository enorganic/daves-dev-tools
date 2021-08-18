#!/usr/bin/env python3
"""
This script updates installation requirements in ../setup.py
"""
from os import chdir
from os.path import abspath, dirname

from setuptools_setup_versions import requirements  # type: ignore

from daves_dev_tools.utilities import run

ROOT_PROJECT_DIRECTORY: str = dirname(dirname(abspath(__file__)))


if __name__ == "__main__":
    # `cd` into the repository's root directory
    chdir(ROOT_PROJECT_DIRECTORY)
    # Update `setup.py` to require currently installed versions of all packages
    requirements.update_setup(
        default_operator="~=",
        ignore={
            "snowflake-connector-python",
            "pyspark",
            "numpy",
            "pandas",
            "pyarrow",
            "boto3",
        },
    )
    run(f"black {ROOT_PROJECT_DIRECTORY}/setup.py")
