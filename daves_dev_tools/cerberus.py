import functools
import logging
import sys
from inspect import Parameter, Signature, signature
from warnings import warn
from collections import OrderedDict
from traceback import format_exception
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Iterable,
    Mapping,
    Union,
)
from .utilities import sys_argv_pop, iter_sys_argv_pop
from .errors import append_exception_text

__all__: List[str] = [
    "get_cerberus_secrets",
    "get_cerberus_secret",
    "apply_sys_argv_cerberus_arguments",
]
lru_cache: Callable[..., Any] = functools.lru_cache


@lru_cache()
def get_cerberus_secrets(
    cerberus_url: str,
    path: str,
) -> Dict[str, str]:
    """
    This function attempts to access Cerberus secrets at the given `path`
    with each AWS profile until successful, or until having run out of
    profiles, and returns the secrets if successful (or raises an error if
    not).

    Parameters:

    - **cerberus_url** (str): The Cerberus API endpoint
    - **path** (str): The Cerberus path containing the desired secret(s)
    """
    try:
        import boto3  # type: ignore
        from botocore.exceptions import (  # type: ignore
            ClientError,
            NoCredentialsError,
        )
        from cerberus import CerberusClientException  # type: ignore
        from cerberus.client import CerberusClient  # type: ignore
    except ImportError as error:
        append_exception_text(
            error,
            (
                'Please install *daves-dev-tools* with the "cerberus" extra: '
                "`pip3 install 'daves-dev-tools[cerberus]'`"
            ),
        )
        raise error
    secrets: Optional[Dict[str, str]] = None
    errors: Dict[str, str] = OrderedDict()
    for profile_name in boto3.Session().available_profiles + [None]:
        arn: str = ""
        try:
            session: boto3.Session = boto3.Session(profile_name=profile_name)
            arn = session.client("sts").get_caller_identity().get("Arn")
            secrets = CerberusClient(
                cerberus_url, aws_session=session
            ).get_secrets_data(path)
            break
        except (CerberusClientException, ClientError, NoCredentialsError):
            errors[arn or profile_name] = "".join(
                format_exception(*sys.exc_info())
            )
    if secrets is None:
        error_text: str = "\n".join(
            f'{key or "[default]"}:\n{value}\n'
            for key, value in errors.items()
        )
        warn(error_text)
        logging.warning(error_text)
        raise PermissionError(
            "No AWS profile was found with access to the requested secrets"
        )
    return secrets


def get_cerberus_secret(cerberus_url: str, path: str) -> Tuple[str, str]:
    """
    This is a convenience function for retrieving individual values from a
    Cerberus secret, and which return both the key (the last part of the
    path), as well as the retrieved secret value, as a `tuple`. This is
    useful under a common scenario where a username is a key in a secrets
    dictionary, and the client application needs both the username as password.

    Parameters:

    - **cerberus_url** (str): The Cerberus API endpoint
    - **path** (str): The Cerberus path containing the desired secret,
      *including* a dictionary key. For example: "path/to/secrets/key".
    """
    assert cerberus_url
    parts: List[str] = path.strip("/").split("/")
    # Ensure the path includes the dictionary key
    assert len(parts) == 4
    key: str = parts.pop()
    # Retrieve the secrets dictionary
    secrets: Dict[str, str] = get_cerberus_secrets(
        cerberus_url, "/".join(parts)
    )
    # Return the key and the value stored at the secret's "key" index
    return key, secrets[key]


def apply_sys_argv_cerberus_arguments(
    url_parameter_name: Iterable[str],
    parameter_map: Union[
        Mapping[str, Iterable[str]],
        Iterable[Tuple[str, Iterable[str]]],
    ],
    argv: Optional[List[str]] = None,
) -> None:
    """
    This function modifies `sys.argv` by performing lookups against a specified
    Cerberus API and inserting the retrieved values into mapped keyword
    argument values.

    Parameters:

    - url_parameter_name (str): The base URL of the Cerberus API.
    - parameter_map ({str: [str]}): Maps final keyword argument names to
      keyword argument names wherein to find Cerberus paths to lookup
      values to pass to the final keyword arguments. Cerberus path keyword
      arguments are removed from `sys.argv` and final keyword arguments are
      inserted into `sys.argv`.
    - argv ([str]) = sys.argv: If provided, this list will be modified instead
      of `sys.argv`.
    """
    if argv is None:
        argv = sys.argv
    parameter_map_items: Iterable[Tuple[str, Iterable[str]]]
    if isinstance(parameter_map, Mapping):
        parameter_map_items = parameter_map.items()
    else:
        parameter_map_items = parameter_map
    cerberus_url: str = sys_argv_pop(  # type: ignore
        keys=url_parameter_name, flag=False
    )
    if cerberus_url:
        key: str
        cerberus_path_keys: Iterable[str]
        for key, cerberus_path_keys in parameter_map_items:
            value: str
            for value in iter_sys_argv_pop(  # type: ignore
                keys=cerberus_path_keys, argv=argv, flag=False
            ):
                argv += [key, get_cerberus_secret(cerberus_url, value)[-1]]


def _merge_function_signature_args_kwargs(
    function_signature: Signature, args: Iterable[Any], kwargs: Dict[str, Any]
) -> None:
    """
    This function merges positional/keyword arguments for a function
    into the keyword argument dictionary
    """
    value: Any
    parameter: Parameter
    if args:
        for parameter, value in zip(
            function_signature.parameters.values(), args
        ):
            assert parameter.kind == Parameter.POSITIONAL_OR_KEYWORD
            kwargs[parameter.name] = value


def _remove_function_signature_inapplicable_kwargs(
    function_signature: Signature, kwargs: Dict[str, Any]
) -> None:
    def get_parameter_name(parameter_: Parameter) -> str:
        return parameter_.name

    key: str
    for key in set(kwargs.keys()) - set(
        map(
            get_parameter_name,
            function_signature.parameters.values(),
        )
    ):
        del kwargs[key]


def apply_cerberus_path_arguments(
    cerberus_url_parameter_name: str = "cerberus_url",
    **cerberus_path_parameter_names: str,
) -> Callable[..., Callable[..., Any]]:
    """
    This decorator maps parameter names. Each key represents the
    name of a parameter in the decorated function which accepts an explicit
    input, and the corresponding mapped value is the name of a second parameter
    which accepts a cerberus path from where a value for the first parameter
    can be retrieved when not explicitly provided.

    Parameters:
    - cerberus_url_parameter_name (str) = "cerberus_url":
      The name of the Cerberus API URL parameter
    - ** (str): All additional keyword map a
      *parameter name* -> *cerberus URL parameter name*
    """

    def decorating_function(
        function: Callable[..., Any]
    ) -> Callable[..., Any]:
        function_signature: Signature = signature(function)

        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            This function wraps the original and performs lookups for
            any parameters for which an argument is not passed
            """
            # First we consolidate the keyword arguments with any arguments
            # which are passed to parameters which can be either positional
            # *or* keyword arguments, and were passed as positional arguments
            _merge_function_signature_args_kwargs(
                function_signature, args, kwargs
            )
            cerberus_url: str = ""
            if cerberus_url_parameter_name in kwargs:
                cerberus_url = kwargs[cerberus_url_parameter_name]
            elif cerberus_url_parameter_name in function_signature.parameters:
                cerberus_url = (
                    function_signature.parameters[
                        cerberus_url_parameter_name
                    ].default
                    or ""
                )
            # For any arguments where we have a cerberus path and do not have
            # an explicitly passed value, perform a lookup in cerberus
            key: str
            for key in set(cerberus_path_parameter_names.keys()) - set(
                kwargs.keys()
            ):
                cerberus_path_key: str = cerberus_path_parameter_names[key]
                if (cerberus_path_key in kwargs) and kwargs[cerberus_path_key]:
                    kwargs[key] = get_cerberus_secret(
                        cerberus_url,
                        kwargs[cerberus_path_key],
                    )[1]
                elif cerberus_path_key in function_signature.parameters:
                    default: Optional[str] = function_signature.parameters[
                        cerberus_path_key
                    ].default
                    if default:
                        kwargs[key] = get_cerberus_secret(
                            cerberus_url,
                            default,
                        )[1]
            # Remove arguments which do not correspond to
            # any of the function's parameter names
            _remove_function_signature_inapplicable_kwargs(
                function_signature, kwargs
            )
            # Execute the wrapped function
            return function(**kwargs)

        return wrapper

    return decorating_function
