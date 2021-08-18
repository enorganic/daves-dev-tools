import functools
from subprocess import getstatusoutput
from typing import Any, Callable, List

__all__: List[str] = ["lru_cache", "run"]
lru_cache: Callable[..., Any] = functools.lru_cache
# For backwards compatibility:
cerberus: Any
try:
    from daves_dev_tools import cerberus
except ImportError:
    cerberus = None


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
        raise OSError(output)
    else:
        output = output.strip()
        if output and echo:
            print(output)
    return output
