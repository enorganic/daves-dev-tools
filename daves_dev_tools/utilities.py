import functools
import runpy
import sys
import os
from pipes import quote
from itertools import chain
from subprocess import getstatusoutput
from typing import Any, Callable, List, Iterable, Sequence, NoReturn

__all__: List[str] = [
    "lru_cache",
    "run",
    "iter_parse_delimited_values",
]
lru_cache: Callable[..., Any] = functools.lru_cache
# For backwards compatibility:
cerberus: Any
try:
    from daves_dev_tools import cerberus
except ImportError:
    cerberus = None


def _iter_parse_delimited_value(value: str, delimiter: str) -> Iterable[str]:
    return value.split(delimiter)


def iter_parse_delimited_values(
    values: Iterable[str], delimiter: str = ","
) -> Iterable[str]:
    """
    This function iterates over input values which have been provided as a
    list or iterable and/or a single string of character-delimited values.
    A typical use-case is parsing multi-value command-line arguments.
    """
    if isinstance(values, str):
        values = (values,)

    def iter_parse_delimited_value_(value: str) -> Iterable[str]:
        return _iter_parse_delimited_value(value, delimiter=delimiter)

    return chain(*map(iter_parse_delimited_value_, values))


def run(command: str, echo: bool = True) -> str:
    """
    This function runs a shell command, raises an error if a non-zero
    exit code is returned, and echo's both the command and output *if*
    the `echo` parameter is `True`.

    Parameters:

    - command (str): A shell command
    - echo (bool) = True: If `True`, the command and the output from the
      command will be printed to stdout
    """
    if echo:
        print(command)
    status: int
    output: str
    status, output = getstatusoutput(command)
    # Create an error if a non-zero exit status is encountered
    if status:
        raise OSError(output if echo else f"$ {command}\n{output}")
    else:
        output = output.strip()
        if output and echo:
            print(output)
    return output


def _dummy_sys_exit(__status: object) -> None:
    return


def run_module_as_main(
    module_name: str,
    arguments: Sequence[str] = (),
    directory: str = ".",
    echo: bool = False,
) -> None:
    """
    This function runs a module as a main entry point, effectively as a CLI,
    but in the same sub-process as the calling function (thereby retaining
    all privileges granted to the current sub-process).

    Parameters:

    - module_name (str)
    - arguments ([str]) = (): The system arguments to pass to this command,
      replacing `sys.argv` while running the module).
    - directory (str) = ".": The directory in which the command should
      be executed (replacing `os.path.curdir` while running the module).
    - echo (bool) = False: If `True`, an equivalent shell command is printed
      to sys.stdout.
    """
    prior_sys_exit: Callable[[object], NoReturn] = sys.exit
    prior_sys_argv: List[str] = sys.argv
    if not isinstance(arguments, list):
        arguments = list(arguments)
    command_sys_argv: List[str] = sys.argv[:1] + arguments
    prior_current_directory: str = os.path.abspath(os.path.curdir)
    os.chdir(directory)
    try:
        if echo:
            print(
                " ".join(
                    map(
                        quote,
                        [sys.executable, "-m", module_name] + arguments,
                    )
                )
            )
        # Plugging a dummy function into `sys.exit` is necessary to avoid CLI
        # tools such as pip from ending the current process
        sys.exit = _dummy_sys_exit  # type: ignore
        sys.argv = command_sys_argv
        runpy.run_module(module_name, run_name="__main__")
    finally:
        sys.exit = prior_sys_exit  # type: ignore
        os.chdir(prior_current_directory)
        sys.argv = prior_sys_argv
