# daves-dev-tools

This project provides command line utilities for performing common python
development tasks.

## Installation

You can install daves-dev-tools with pip:

```shell
pip3 install daves-dev-tools
```

In order to use some features of this library, you will need to specify
one or more *extras*:

- "cerberus": This extra installs requirements needed in order to import
  `daves_dev_tools.cerberus`, which provides utilities for interacting
  with a [Cerberus](https://engineering.nike.com/cerberus/) vault.

  ```shell
  pip3 install daves-dev-tools[cerberus]
  ```

To install this project for development of *this library*,
clone this repository (replacing "~/Code", below, with the directory
under which you want your project to reside), then run `make`:

```shell script
cd ~/Code && \
git clone\
 https://github.com/enorganic/daves-dev-tools.git\
 daves-dev-tools && \
cd daves-dev-tools && \
make
```
  
## Usage

### Command Line Interface

#### daves-dev-tools clean

This command removes all files from your project directory which are ignored
by git, excepting IDE configuration files (".vscode" and ".idea") and
any explicitly excluded directories (see the CLI help text below).

```shell script
$ daves-dev-tools clean -h
usage: daves-dev-tools [-h] [--exclude EXCLUDE] [root]

positional arguments:
  root                  The root directory path for the project.

optional arguments:
  -h, --help            show this help message and exit
  --exclude EXCLUDE, -e EXCLUDE
                        A path list of sub-directories to exclude (separated
                        by ":" or ";", depending on the operating system).
```

#### daves-dev-tools distribute

```text
$ daves-dev-tools distribute -h
usage: daves-dev-tools distribute [-h] [-cu CERBERUS_URL]
                    [-cup CERBERUS_USERNAME_PATH]
                    [-cpp CERBERUS_PASSWORD_PATH]
                    [-r REPOSITORY] [--repository-url REPOSITORY_URL]
                    [-s] [--sign-with SIGN_WITH] [-i IDENTITY] [-u USERNAME]
                    [-p PASSWORD] [--non-interactive] [-c COMMENT]
                    [--config-file CONFIG_FILE] [--skip-existing]
                    [--cert path] [--client-cert path] [--verbose]
                    [--disable-progress-bar]
                    dist [dist ...]

positional arguments:
  dist                  The distribution files to upload to the repository
                        (package index). Usually dist/* . May additionally
                        contain a .asc file to include an existing signature
                        with the file upload.

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
  -cu CERBERUS_URL, --cerberus-url CERBERUS_URL
                        The base URL of a Cerberus REST API.
                        See: https://swoo.sh/3DBW2Vb
  -cup CERBERUS_USERNAME_PATH, --cerberus-username-path CERBERUS_USERNAME_PATH
                        A Cerberus secure data path (including /key) wherein a
                        username with which to authenticate can be found.
                        See: https://swoo.sh/3DBW2Vb
  -cpp CERBERUS_PASSWORD_PATH, --cerberus-password-path CERBERUS_PASSWORD_PATH
                        A Cerberus secure data path (including /key) wherein a
                        password with which to authenticate can be found.
                        If no USERNAME or CERBERUS_USERNAME_PATH is provided,
                        the last part of this path 
                        (the secure data path entry key) is inferred as your
                        username. See: https://swoo.sh/3DBW2Vb
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

positional arguments:
  requirement           One or more requirement specifiers or configuration
                        file paths

optional arguments:
  -h, --help            show this help message and exit
  -e EXCLUDE, --exclude EXCLUDE
                        A comma-separated list of distributions to exclude
                        from the output
  -er EXCLUDE_RECURSIVE, --exclude-recursive EXCLUDE_RECURSIVE
                        A comma-separated list of distributions to exclude
                        from the output, along with any/all requirements which
                        might have been recursively discovered for these
                        packages
  -nv NO_VERSION, --no-version NO_VERSION
                        Don't include the version (only output distribution
                        names) for packages matching this glob pattern (note:
                        the value must be single-quoted if it contain
                        wildcards)
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

### daves-dev-tools uninstall-all

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

#### daves-dev-tools install-editable

```
$ daves-dev-tools install-editable -h
usage: daves-dev-tools install-editable [-h] [-d DIRECTORY] [-e EXCLUDE] [-edre EXCLUDE_DIRECTORY_REGULAR_EXPRESSION] [-dr]
                                        [-ie]
                                        [requirement [requirement ...]]

This command will attempt to find and install, in develop (editable) mode, all packages which are installed in the current
python environment. If one or more `requirement` file paths or specifiers are provided, installation will be limited to the
dependencies identified (recursively) by these requirements. Exclusions can be specified using the `-e` parameter. Directories
can be excluded by passing regular expressions to the `-edre` parameter.

positional arguments:
  requirement           One or more requirement specifiers or configuration file paths. If provided, only dependencies of these
                        requirements will be installed.

optional arguments:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        A directory in which to search for requirements. By default, the directory above the current directory
                        is searched. This argument may be passed more than once to include multiple locations.
  -e EXCLUDE, --exclude EXCLUDE
                        A comma-separated list of distribution names to exclude
  -edre EXCLUDE_DIRECTORY_REGULAR_EXPRESSION, --exclude-directory-regular-expression EXCLUDE_DIRECTORY_REGULAR_EXPRESSION
                        Directories matching this regular expression will be excluded when searching for setup locations This
                        argument may be passed more than once to exclude directories matching more than one regular expression.
                        The default for this argument is equivalent to `-edre '^[.~].*$' -edre '^venv$' -edre '^site-packages$'`
  -dr, --dry-run        Print, but do not execute, all `pip install` commands
  -ie, --include-extras
                        Install all extras for all discovered distributions
```
