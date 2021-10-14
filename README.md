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

```
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

```
$ daves-dev-tools distribute -h
usage: daves-dev-tools distribute [-h] [-r REPOSITORY] [--repository-url REPOSITORY_URL]
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
```

#### daves-dev-tools requirements update

```
$ daves-dev-tools requirements update -h
usage: daves-dev-tools requirements update [-h] [-i IGNORE]
                                           [-aen ALL_EXTRA_NAME]
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

```
$ daves-dev-tools requirements freeze -h
usage: daves-dev-tools requirements freeze [-h] [-e EXCLUDE] [-r REQUIREMENT] requirement_specifier [requirement_specifier ...]

positional arguments:
  requirement_specifier
                        One or more requirement specifiers

optional arguments:
  -h, --help            show this help message and exit
  -e EXCLUDE, --exclude EXCLUDE
                        A comma-separated list of distributions to exclude from the output. Please note that excluding a distribution also
                        excludes any/all requirements which might be recursively discovered for that package.
  -r REQUIREMENT, --requirement REQUIREMENT
                        The local file path of a requirements file
```

#### daves-dev-tools git download

(WIP)

#### daves-dev-tools wheel bundle

(WIP)
