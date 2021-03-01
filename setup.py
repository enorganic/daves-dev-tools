import re
import sys
from collections import OrderedDict
from itertools import chain
from typing import (
    Dict,
    Iterable,
    Match,
    Optional,
    Pattern,
    Sequence,
    Set,
    Any,
)

import setuptools  # type: ignore

_INSTALL_REQUIRES: str = "install_requires"


_extras_pattern: Pattern = re.compile(r"^([^\[]+\[)([^\]]+)(\].*)$")


def consolidate_requirement_options(
    requirements: Iterable[str],
) -> Iterable[str]:
    template: str
    requirement: str
    templates_options: Dict[str, Set[str]] = OrderedDict()
    traversed_requirements: Set[str] = set()
    for requirement in requirements:
        match: Optional[Match] = _extras_pattern.match(requirement)
        if match:
            groups: Sequence[str] = match.groups()
            no_extras_requirement: str = f"{groups[0][:-1]}{groups[2][1:]}"
            template = f"{groups[0]}{{}}{groups[2]}"
            if template not in templates_options:
                templates_options[template] = set()
            templates_options[template] |= set(groups[1].split(","))
            if no_extras_requirement in templates_options:
                del templates_options[no_extras_requirement]
        elif requirement not in traversed_requirements:
            templates_options[requirement] = set()
    options: Set[str]
    for template, options in templates_options.items():
        if options:
            yield template.format(",".join(sorted(options)))
        else:
            yield template


def setup(**kwargs: Any) -> None:
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
    if "extras_require" in kwargs:
        if "all" not in kwargs["extras_require"]:
            kwargs["extras_require"]["all"] = list(
                consolidate_requirement_options(
                    chain(
                        *(
                            values
                            for key, values in kwargs["extras_require"].items()
                            if key not in ("dev", "test")
                        )
                    )
                )
            )
        kwargs["extras_require"]["test"] = list(
            consolidate_requirement_options(
                chain(
                    *(
                        values
                        for key, values in kwargs["extras_require"].items()
                        if key not in ("dev", "all")
                    )
                )
            )
        )
        print(
            "extras_require[all]:\n"
            + "\n".join(
                f"- {requirement}"
                for requirement in kwargs["extras_require"]["all"]
            )
        )
        print(
            "extras_require[test]:\n"
            + "\n".join(
                f"- {requirement}"
                for requirement in kwargs["extras_require"]["test"]
            )
        )
    # Pass the modified keyword arguments to `setuptools.setup`
    setuptools.setup(**kwargs)


setup(
    name="daves-dev-tools",
    version="0.3.2",
    description="Dave's Dev Tools",
    author="David Belais",
    author_email="david@belais.me",
    python_requires="~=3.6",
    packages=["daves_dev_tools", "daves_dev_tools.utilities"],
    package_data={
        "daves_dev_tools": ["py.typed"],
        "daves_dev_tools.utilities": ["py.typed"],
    },
    install_requires=["twine~=3.2", "wheel~=0.36"],
    extras_require={
        "cerberus": ["cerberus-python-client~=2.5"],
        "dev": [
            "readme-md-docstrings>=0.1.0,<1",
            "setuptools-setup-versions>=1.4.1,<2",
        ],
        "test": [
            "black~=19.10b0",
            "pytest~=5.4",
            "tox~=3.20",
            "flake8~=3.8",
            "mypy~=0.790",
            "pip>=20.3.1",
        ],
    },
    entry_points={
        "console_scripts": ["daves-dev-tools = daves_dev_tools.__main__:main"]
    },
)
