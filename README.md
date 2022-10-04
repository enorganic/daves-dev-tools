# daves-dev-tools

[![tests](https://github.com/enorganic/daves-dev-tools/actions/workflows/test-distribute.yml/badge.svg?branch=main)](https://github.com/enorganic/daves-dev-tools/actions/workflows/test-distribute.yml)
[![CodeQL](https://github.com/enorganic/daves-dev-tools/actions/workflows/codeql-analysis.yml/badge.svg?branch=main)](https://github.com/enorganic/daves-dev-tools/actions/workflows/codeql-analysis.yml)

This project provides command line utilities for performing common python
development tasks.

## Installation

You can install daves-dev-tools with pip:

```shell
pip3 install daves-dev-tools
```

## Usage

### Command Line Interface

```text
$ daves-dev-tools % daves-dev-tools -h
Usage:
  daves-dev-tools <command> [options]

Commands:
  git                         Tools for interacting with git repos.
  requirements                Tools for managing requirement versions.
  install-editable            Auto-discover and install packages in "develop"
                              mode used by the current environment or by one or
                              more specified packages/projects.
  make-typed                  Configure your project to indicate to `mypy` that
                              the contents are type-hinted.
  uninstall-all               Uninstall all distributions from the current
                              python environment except for those explicitly
                              specified (and their dependencies).
  clean                       Delete files from your project which are ignored
                              by `git`, excepting files matching specified
                              exclusion patterns.
  distribute                  Build and distribute to PYPI (or other indexes)
                              with one command.
```

#### daves-dev-tools requirements update

Example:

```shell script
daves-dev-tools requirements update -aen all setup.cfg pyproject.toml tox.ini
```

The above command will update version specifiers for
all package requirements in your setup.cfg, pyproject.toml, and tox.ini files
to match currently installed versions of each distribution (matching existing
granularity, and only for *inclusive* specifiers—so where the comparator is
"~=", "==", ">=", or "<="—but not ">", "<", or "!=").

Help:

```text
$ daves-dev-tools requirements update -h
usage: daves-dev-tools requirements update [-h] [-i IGNORE]
                                           [-aen ALL_EXTRA_NAME] [-v]
                                           path [path ...]

positional arguments:
  path                  One or more local paths to a *setup.cfg* and/or
                        *requirements.txt* file

optional arguments:
  -h, --help            show this help message and exit
  -i IGNORE, --ignore IGNORE
                        A comma-separated list of distributions to ignore
                        (leave any requirements pertaining to the package as-
                        is)
  -aen ALL_EXTRA_NAME, --all-extra-name ALL_EXTRA_NAME
                        If provided, an extra which consolidates the
                        requirements for all other extras will be
                        added/updated to *setup.cfg* (this argument is ignored
                        for *requirements.txt* files)
  -v, --verbose         Echo more verbose output
```

#### daves-dev-tools requirements freeze

```text
$ daves-dev-tools requirements freeze -h
usage: daves-dev-tools requirements freeze [-h] [-e EXCLUDE]
                                           [-er EXCLUDE_RECURSIVE]
                                           [-nv NO_VERSION]
                                           requirement [requirement ...]

This command prints dependencies inferred from an installed distribution or
project, in a similar format to the output of `pip freeze`, except that all
generated requirements are specified in the format "distribution-name==0.0.0"
(including for editable installations). Using this command instead of `pip
freeze` to generate requirement files ensures that you don't bloat your
requirements files with superfluous distributions.

positional arguments:
  requirement           One or more requirement specifiers (for example:
                        "requirement-name", "requirement-
                        name[extra-a,extra-b]", ".[extra-a, extra-b]" or
                        "../other-editable-package-directory[extra-a,
                        extra-b]) and/or paths to a setup.py, setup.cfg,
                        pyproject.toml, tox.ini or requirements.txt file

optional arguments:
  -h, --help            show this help message and exit
  -e EXCLUDE, --exclude EXCLUDE
                        A distribution (or comma-separated list of
                        distributions) to exclude from the output
  -er EXCLUDE_RECURSIVE, --exclude-recursive EXCLUDE_RECURSIVE
                        A distribution (or comma-separated list of
                        distributions) to exclude from the output. Unlike -e /
                        --exclude, this argument also precludes recursive
                        requirement discovery for the specified packages,
                        thereby excluding all of the excluded package's
                        requirements which are not required by another (non-
                        excluded) distribution.
  -nv NO_VERSION, --no-version NO_VERSION
                        Don't include versions (only output distribution
                        names) for packages matching this glob pattern (note:
                        the value must be single-quoted if it contain
                        wildcards)
```

#### daves-dev-tools install-editable

```text
$ daves-dev-tools install-editable -h
usage: daves-dev-tools install-editable [-h] [-r REQUIREMENT] [-d DIRECTORY]
                                        [-e EXCLUDE] [-ed EXCLUDE_DIRECTORY]
                                        [-edre EXCLUDE_DIRECTORY_REGULAR_EXPRESSION]
                                        [-dr] [-ie]

This command will attempt to find and install, in develop (editable) mode, all
packages which are installed in the current python environment. If one or more
`requirement` file paths or specifiers are provided, installation will be
limited to the dependencies identified (recursively) by these requirements.
Exclusions can be specified using the `-e` parameter. Directories can be
excluded by passing regular expressions to the `-edre` parameter. Any
arguments passed not matching those specified below will be passed on to `pip
install` (see `pip install -h` for additionally available arguments).

optional arguments:
  -h, --help            show this help message and exit
  -r REQUIREMENT, --requirement REQUIREMENT
                        One or more requirement specifiers, requirement file
                        paths, or configuration file paths (setup.cfg,
                        setup.py, pyproject.toml, tox.ini, etc.). If provided,
                        only dependencies of these requirements will be
                        installed.
  -d DIRECTORY, --directory DIRECTORY
                        A directory in which to search for requirements. By
                        default, the directory above the current directory is
                        searched. This argument may be passed more than once
                        to include multiple locations.
  -e EXCLUDE, --exclude EXCLUDE
                        A comma-separated list of distribution names to
                        exclude
  -ed EXCLUDE_DIRECTORY, --exclude-directory EXCLUDE_DIRECTORY
                        One or more glob patterns indicating directories to
                        exclude. This argument may be expressed as a path
                        relative to the current.
  -edre EXCLUDE_DIRECTORY_REGULAR_EXPRESSION, --exclude-directory-regular-expression EXCLUDE_DIRECTORY_REGULAR_EXPRESSION
                        Directories matching this regular expression will be
                        excluded when searching for setup locations This
                        argument may be passed more than once to exclude
                        directories matching more than one regular expression.
                        The default for this argument is equivalent to `-edre
                        '^[.~].*$' -edre '^venv$' -edre '^site-packages$'`.
                        Unlike for *--exclude-directory*, these expressions
                        apply only to the directory *name*, and no attempt to
                        resolve relative paths is made.
  -dr, --dry-run        Print, but do not execute, all `pip install` commands
  -ie, --include-extras
                        Install all extras for all discovered distributions
```

#### daves-dev-tools make-typed

```text
$ daves-dev-tools make-typed -h
usage: daves-dev-tools make-typed [-h] path

Add **/py.typed files and alter the setup.cfg such that a distribution's packages will be identifiable as fully type-hinted

positional arguments:
  path        A project directory (where the setup.py and/or setup.cfg file are located)

optional arguments:
  -h, --help  show this help message and exit
```

#### daves-dev-tools uninstall-all

```text
$ daves-dev-tools uninstall-all -h
usage: daves-dev-tools uninstall-all [-h] [-e EXCLUDE] [-dr]

This command will uninstall all distributions installed in the same environment as that from which this command is executed,
excluding any specified by `-e EXCLUDE`.

optional arguments:
  -h, --help            show this help message and exit
  -e EXCLUDE, --exclude EXCLUDE
                        One or more distribution specifiers, requirement files, setup.cfg files, pyproject.toml files, or
                        tox.ini files denoting packages to exclude (along with all of their requirements) from those
                        distributions to be uninstalled
  -dr, --dry-run        Print, but do not execute, the assembled `pip uninstall` command which, absent this flag, would be
                        executed
```

#### daves-dev-tools git download

```text
$ daves-dev-tools git download -h
usage: daves-dev-tools git download [-h] [-b BRANCH] [-d DIRECTORY] [-e]
                                    repo [file [file ...]]

Download files from a git repository matching one or more specified file names
or glob patterns

positional arguments:
  repo                  Reference repository
  file                  One or more `glob` pattern(s) indicating a specific
                        file or files to include. If not provided, all files
                        in the repository will be included.

optional arguments:
  -h, --help            show this help message and exit
  -b BRANCH, --branch BRANCH
                        Retrieve files from BRANCH instead of the remote's
                        HEAD
  -d DIRECTORY, --directory DIRECTORY
                        The directory under which to save matched files. If
                        not provided, files will be saved under the current
                        directory.
  -e, --echo            Print the downloaded file paths
```

#### daves-dev-tools git tag-version

```text
$ daves-dev-tools git tag-version -h
usage: daves-dev-tools git tag-version [-h] [-m MESSAGE] [directory]

Tag your repo with the python package version, if a tag for that version
doesn't already exist.

positional arguments:
  directory             Your project directory. If not provided, the current
                        directory will be used.

optional arguments:
  -h, --help            show this help message and exit
  -m MESSAGE, --message MESSAGE
                        The tag message. If not provided, the new version
                        number is used.
```

#### daves-dev-tools clean

```text
$ daves-dev-tools clean -h
usage: daves-dev-tool clean [-h] [-e EXCLUDE] [-dr] [directory]

This command removes all files from your project directory which are ignored
by git, unless matching one of the EXCLUDE glob patterns.

positional arguments:
  directory             The root directory for the project.

optional arguments:
  -h, --help            show this help message and exit
  -e EXCLUDE, --exclude EXCLUDE
                        One or more glob patterns indicating files/directories
                        to exclude from cleanup. The default values are: `-e
                        .idea -e .vscode -e .git -e venv`.
  -dr, --dry-run        Instead of executing the cleanup, just print the shell
                        commands (a list of `rm FILE` commands).
```

#### daves-dev-tools distribute

```text
$ daves-dev-tools distribute -h
usage: daves-dev-tools distribute [-h]
                    [-r REPOSITORY] [--repository-url REPOSITORY_URL]
                    [-s] [--sign-with SIGN_WITH] [-i IDENTITY] [-u USERNAME]
                    [-p PASSWORD] [--non-interactive] [-c COMMENT]
                    [--config-file CONFIG_FILE] [--skip-existing]
                    [--cert path] [--client-cert path] [--verbose]
                    [--disable-progress-bar]
                    [directory]

positional arguments:
  directory             The root directory path for the project.

optional arguments:
  -h, --help            show this help message and exit
  -r REPOSITORY, --repository REPOSITORY
                        The repository (package index) to upload the package
                        to. Should be a section in the config file (default:
                        pypi). (Can also be set via TWINE_REPOSITORY
                        environment variable.)
  --repository-url REPOSITORY_URL
                        The repository (package index) URL to upload the
                        package to. This overrides --repository. (Can also be
                        set via TWINE_REPOSITORY_URL environment variable.)
  -s, --sign            Sign files to upload using GPG.
  --sign-with SIGN_WITH
                        GPG program used to sign uploads (default: gpg).
  -i IDENTITY, --identity IDENTITY
                        GPG identity used to sign files.
  -u USERNAME, --username USERNAME
                        The username to authenticate to the repository
                        (package index) as. (Can also be set via
                        TWINE_USERNAME environment variable.)
  -p PASSWORD, --password PASSWORD
                        The password to authenticate to the repository
                        (package index) with. (Can also be set via
                        TWINE_PASSWORD environment variable.)
  --non-interactive     Do not interactively prompt for username/password if
                        the required credentials are missing. (Can also be set
                        via TWINE_NON_INTERACTIVE environment variable.)
  -c COMMENT, --comment COMMENT
                        The comment to include with the distribution file.
  --config-file CONFIG_FILE
                        The .pypirc config file to use.
  --skip-existing       Continue uploading files if one already exists. (Only
                        valid when uploading to PyPI. Other implementations
                        may not support this.)
  --cert path           Path to alternate CA bundle (can also be set via
                        TWINE_CERT environment variable).
  --client-cert path    Path to SSL client certificate, a single file
                        containing the private key and the certificate in PEM
                        format.
  --verbose             Show verbose output.
  --disable-progress-bar
                        Disable the progress bar.
```
