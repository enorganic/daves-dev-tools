import sys
from typing import Set

import setuptools

_INSTALL_REQUIRES: str = "install_requires"


def setup(**kwargs) -> None:
    """
    This `setup` script intercepts arguments to be passed to
    `setuptools.setup` in order to dynamically alter setup requirements
    while retaining a function call which can be easily parsed and altered
    by `setuptools-setup-versions`.
    """
    # Require the package "dataclasses" for python 3.6, but not later
    # python versions (since it's part of the standard library after 3.6)
    if sys.version_info[:2] == (3, 6):
        if _INSTALL_REQUIRES not in kwargs:
            kwargs[_INSTALL_REQUIRES] = []
        kwargs[_INSTALL_REQUIRES].append("dataclasses")
    # Add an "all" extra which includes all extra requirements
    if "extras_require" in kwargs and "all" not in kwargs["extras_require"]:
        all_extras_require: Set[str] = set()
        kwargs["extras_require"]["all"] = []
        for extra_name, requirements in kwargs["extras_require"].items():
            if extra_name != "all":
                for requirement in requirements:
                    if requirement not in all_extras_require:
                        all_extras_require.add(requirement)
                        kwargs["extras_require"]["all"].append(requirement)
    # Pass the modified keyword arguments to `setuptools.setup`
    setuptools.setup(**kwargs)


setup(
    name="daves-dev-tools",
    version="0.0.23",
    description="Dave's Dev Tools",
    author="David Belais",
    author_email="david@belais.me",
    python_requires="~=3.6",
    packages=["daves_dev_tools", "daves_dev_tools.utilities"],
    package_data={
        "daves_dev_tools": ["py.typed"],
        "daves_dev_tools.utilities": ["py.typed"],
    },
    install_requires=["twine~=3.2", "wheel~=0.35"],
    extras_require={
        "cerberus": ["cerberus-python-client~=2.5", "boto3~=1.4"],
        "dev": [
            "black~=19.10b0",
            "readme-md-docstrings>=0.1.0,<1",
            "setuptools-setup-versions>=1.4.1,<2",
        ],
        "test": ["pytest~=5.4", "tox~=3.20", "flake8~=3.8", "mypy~=0.790"],
    },
    entry_points={
        "console_scripts": ["daves-dev-tools = daves_dev_tools.__main__:main"]
    },
)
