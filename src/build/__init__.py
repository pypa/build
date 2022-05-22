# SPDX-License-Identifier: MIT

"""
build - A simple, correct PEP 517 build frontend
"""

__version__ = '0.8.0'

import contextlib
import difflib
import logging
import os
import re
import subprocess
import sys
import textwrap
import types
import warnings
import zipfile

from collections import OrderedDict
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)

import pep517.wrappers


TOMLDecodeError: Type[Exception]
toml_loads: Callable[[str], MutableMapping[str, Any]]

if sys.version_info >= (3, 11):
    from tomllib import TOMLDecodeError
    from tomllib import loads as toml_loads
else:
    try:
        from tomli import TOMLDecodeError
        from tomli import loads as toml_loads
    except ModuleNotFoundError:  # pragma: no cover
        from toml import TomlDecodeError as TOMLDecodeError  # type: ignore[import,no-redef]
        from toml import loads as toml_loads  # type: ignore[no-redef]


RunnerType = Callable[[Sequence[str], Optional[str], Optional[Mapping[str, str]]], None]
ConfigSettingsType = Mapping[str, Union[str, Sequence[str]]]
PathType = Union[str, 'os.PathLike[str]']
_ExcInfoType = Union[Tuple[Type[BaseException], BaseException, types.TracebackType], Tuple[None, None, None]]


_WHEEL_NAME_REGEX = re.compile(
    r'(?P<distribution>.+)-(?P<version>.+)'
    r'(-(?P<build_tag>.+))?-(?P<python_tag>.+)'
    r'-(?P<abi_tag>.+)-(?P<platform_tag>.+)\.whl'
)


_DEFAULT_BACKEND = {
    'build-backend': 'setuptools.build_meta:__legacy__',
    'requires': ['setuptools >= 40.8.0', 'wheel'],
}


_logger = logging.getLogger(__name__)


class BuildException(Exception):
    """
    Exception raised by :class:`ProjectBuilder`
    """


class BuildBackendException(Exception):
    """
    Exception raised when a backend operation fails
    """

    def __init__(
        self, exception: Exception, description: Optional[str] = None, exc_info: _ExcInfoType = (None, None, None)
    ) -> None:
        super().__init__()
        self.exception = exception
        self.exc_info = exc_info
        self._description = description

    def __str__(self) -> str:
        if self._description:
            return self._description
        return f'Backend operation failed: {self.exception!r}'


class BuildSystemTableValidationError(BuildException):
    """
    Exception raised when the ``[build-system]`` table in pyproject.toml is invalid.
    """

    def __str__(self) -> str:
        return f'Failed to validate `build-system` in pyproject.toml: {self.args[0]}'


class FailedProcessError(Exception):
    """
    Exception raised when an setup or prepration operation fails.
    """

    def __init__(self, exception: subprocess.CalledProcessError, description: str) -> None:
        super().__init__()
        self.exception = exception
        self._description = description

    def __str__(self) -> str:
        cmd = ' '.join(self.exception.cmd)
        description = f"{self._description}\n  Command '{cmd}' failed with return code {self.exception.returncode}"
        for stream_name in ('stdout', 'stderr'):
            stream = getattr(self.exception, stream_name)
            if stream:
                description += f'\n  {stream_name}:\n'
                description += textwrap.indent(stream.decode(), '    ')
        return description


class TypoWarning(Warning):
    """
    Warning raised when a possible typo is found
    """


@contextlib.contextmanager
def _working_directory(path: str) -> Iterator[None]:
    current = os.getcwd()

    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(current)


def _validate_source_directory(srcdir: PathType) -> None:
    if not os.path.isdir(srcdir):
        raise BuildException(f'Source {srcdir} is not a directory')
    pyproject_toml = os.path.join(srcdir, 'pyproject.toml')
    setup_py = os.path.join(srcdir, 'setup.py')
    if not os.path.exists(pyproject_toml) and not os.path.exists(setup_py):
        raise BuildException(f'Source {srcdir} does not appear to be a Python project: no pyproject.toml or setup.py')


def check_dependency(
    req_string: str, ancestral_req_strings: Tuple[str, ...] = (), parent_extras: AbstractSet[str] = frozenset()
) -> Iterator[Tuple[str, ...]]:
    """
    Verify that a dependency and all of its dependencies are met.

    :param req_string: Requirement string
    :param parent_extras: Extras (eg. "test" in myproject[test])
    :yields: Unmet dependencies
    """
    import packaging.requirements

    if sys.version_info >= (3, 8):
        import importlib.metadata as importlib_metadata
    else:
        import importlib_metadata

    req = packaging.requirements.Requirement(req_string)

    if req.marker:
        extras = frozenset(('',)).union(parent_extras)
        # a requirement can have multiple extras but ``evaluate`` can
        # only check one at a time.
        if all(not req.marker.evaluate(environment={'extra': e}) for e in extras):
            # if the marker conditions are not met, we pretend that the
            # dependency is satisfied.
            return

    try:
        dist = importlib_metadata.distribution(req.name)  # type: ignore[no-untyped-call]
    except importlib_metadata.PackageNotFoundError:
        # dependency is not installed in the environment.
        yield ancestral_req_strings + (req_string,)
    else:
        if req.specifier and not req.specifier.contains(dist.version, prereleases=True):
            # the installed version is incompatible.
            yield ancestral_req_strings + (req_string,)
        elif dist.requires:
            for other_req_string in dist.requires:
                # yields transitive dependencies that are not satisfied.
                yield from check_dependency(other_req_string, ancestral_req_strings + (req_string,), req.extras)


def _find_typo(dictionary: Mapping[str, str], expected: str) -> None:
    for obj in dictionary:
        if difflib.SequenceMatcher(None, expected, obj).ratio() >= 0.8:
            warnings.warn(
                f"Found '{obj}' in pyproject.toml, did you mean '{expected}'?",
                TypoWarning,
            )


def _parse_build_system_table(pyproject_toml: Mapping[str, Any]) -> Dict[str, Any]:
    # If pyproject.toml is missing (per PEP 517) or [build-system] is missing
    # (per PEP 518), use default values
    if 'build-system' not in pyproject_toml:
        _find_typo(pyproject_toml, 'build-system')
        return _DEFAULT_BACKEND

    build_system_table = dict(pyproject_toml['build-system'])

    # If [build-system] is present, it must have a ``requires`` field (per PEP 518)
    if 'requires' not in build_system_table:
        _find_typo(build_system_table, 'requires')
        raise BuildSystemTableValidationError('`requires` is a required property')
    elif not isinstance(build_system_table['requires'], list) or not all(
        isinstance(i, str) for i in build_system_table['requires']
    ):
        raise BuildSystemTableValidationError('`requires` must be an array of strings')

    if 'build-backend' not in build_system_table:
        _find_typo(build_system_table, 'build-backend')
        # If ``build-backend`` is missing, inject the legacy setuptools backend
        # but leave ``requires`` intact to emulate pip
        build_system_table['build-backend'] = _DEFAULT_BACKEND['build-backend']
    elif not isinstance(build_system_table['build-backend'], str):
        raise BuildSystemTableValidationError('`build-backend` must be a string')

    if 'backend-path' in build_system_table and (
        not isinstance(build_system_table['backend-path'], list)
        or not all(isinstance(i, str) for i in build_system_table['backend-path'])
    ):
        raise BuildSystemTableValidationError('`backend-path` must be an array of strings')

    unknown_props = build_system_table.keys() - {'requires', 'build-backend', 'backend-path'}
    if unknown_props:
        raise BuildSystemTableValidationError(f'Unknown properties: {", ".join(unknown_props)}')

    return build_system_table


class ProjectBuilder:
    """
    The PEP 517 consumer API.
    """

    def __init__(
        self,
        srcdir: PathType,
        python_executable: str = sys.executable,
        scripts_dir: Optional[str] = None,
        runner: RunnerType = pep517.wrappers.default_subprocess_runner,
    ) -> None:
        """
        :param srcdir: The source directory
        :param scripts_dir: The location of the scripts dir (defaults to the folder where the python executable lives)
        :param python_executable: The python executable where the backend lives
        :param runner: An alternative runner for backend subprocesses

        The 'runner', if provided, must accept the following arguments:

        - cmd: a list of strings representing the command and arguments to
          execute, as would be passed to e.g. 'subprocess.check_call'.
        - cwd: a string representing the working directory that must be
          used for the subprocess. Corresponds to the provided srcdir.
        - extra_environ: a dict mapping environment variable names to values
          which must be set for the subprocess execution.

        The default runner simply calls the backend hooks in a subprocess, writing backend output
        to stdout/stderr.
        """
        self.srcdir: str = os.path.abspath(srcdir)
        _validate_source_directory(srcdir)

        spec_file = os.path.join(srcdir, 'pyproject.toml')

        try:
            with open(spec_file, 'rb') as f:
                spec = toml_loads(f.read().decode())
        except FileNotFoundError:
            spec = {}
        except PermissionError as e:
            raise BuildException(f"{e.strerror}: '{e.filename}' ")
        except TOMLDecodeError as e:
            raise BuildException(f'Failed to parse {spec_file}: {e} ')

        self._build_system = _parse_build_system_table(spec)
        self._backend = self._build_system['build-backend']
        self._scripts_dir = scripts_dir
        self._hook_runner = runner
        self._hook = pep517.wrappers.Pep517HookCaller(
            self.srcdir,
            self._backend,
            backend_path=self._build_system.get('backend-path'),
            python_executable=python_executable,
            runner=self._runner,
        )

    def _runner(
        self, cmd: Sequence[str], cwd: Optional[str] = None, extra_environ: Optional[Mapping[str, str]] = None
    ) -> None:
        # if script dir is specified must be inserted at the start of PATH (avoid duplicate path while doing so)
        if self.scripts_dir is not None:
            paths: Dict[str, None] = OrderedDict()
            paths[str(self.scripts_dir)] = None
            if 'PATH' in os.environ:
                paths.update((i, None) for i in os.environ['PATH'].split(os.pathsep))
            extra_environ = {} if extra_environ is None else dict(extra_environ)
            extra_environ['PATH'] = os.pathsep.join(paths)
        self._hook_runner(cmd, cwd, extra_environ)

    @property
    def python_executable(self) -> str:
        """
        The Python executable used to invoke the backend.
        """
        # make mypy happy
        exe: str = self._hook.python_executable
        return exe

    @python_executable.setter
    def python_executable(self, value: str) -> None:
        self._hook.python_executable = value

    @property
    def scripts_dir(self) -> Optional[str]:
        """
        The folder where the scripts are stored for the python executable.
        """
        return self._scripts_dir

    @scripts_dir.setter
    def scripts_dir(self, value: Optional[str]) -> None:
        self._scripts_dir = value

    @property
    def build_system_requires(self) -> Set[str]:
        """
        The dependencies defined in the ``pyproject.toml``'s
        ``build-system.requires`` field or the default build dependencies
        if ``pyproject.toml`` is missing or ``build-system`` is undefined.
        """
        return set(self._build_system['requires'])

    def get_requires_for_build(self, distribution: str, config_settings: Optional[ConfigSettingsType] = None) -> Set[str]:
        """
        Return the dependencies defined by the backend in addition to
        :attr:`build_system_requires` for a given distribution.

        :param distribution: Distribution to get the dependencies of
            (``sdist`` or ``wheel``)
        :param config_settings: Config settings for the build backend
        """
        self.log(f'Getting dependencies for {distribution}...')
        hook_name = f'get_requires_for_build_{distribution}'
        get_requires = getattr(self._hook, hook_name)

        with self._handle_backend(hook_name):
            return set(get_requires(config_settings))

    def check_dependencies(
        self, distribution: str, config_settings: Optional[ConfigSettingsType] = None
    ) -> Set[Tuple[str, ...]]:
        """
        Return the dependencies which are not satisfied from the combined set of
        :attr:`build_system_requires` and :meth:`get_requires_for_build` for a given
        distribution.

        :param distribution: Distribution to check (``sdist`` or ``wheel``)
        :param config_settings: Config settings for the build backend
        :returns: Set of variable-length unmet dependency tuples
        """
        dependencies = self.get_requires_for_build(distribution, config_settings).union(self.build_system_requires)
        return {u for d in dependencies for u in check_dependency(d)}

    def prepare(
        self, distribution: str, output_directory: PathType, config_settings: Optional[ConfigSettingsType] = None
    ) -> Optional[str]:
        """
        Prepare metadata for a distribution.

        :param distribution: Distribution to build (must be ``wheel``)
        :param output_directory: Directory to put the prepared metadata in
        :param config_settings: Config settings for the build backend
        :returns: The full path to the prepared metadata directory
        """
        self.log(f'Getting metadata for {distribution}...')
        try:
            return self._call_backend(
                f'prepare_metadata_for_build_{distribution}',
                output_directory,
                config_settings,
                _allow_fallback=False,
            )
        except BuildBackendException as exception:
            if isinstance(exception.exception, pep517.wrappers.HookMissing):
                return None
            raise

    def build(
        self,
        distribution: str,
        output_directory: PathType,
        config_settings: Optional[ConfigSettingsType] = None,
        metadata_directory: Optional[str] = None,
    ) -> str:
        """
        Build a distribution.

        :param distribution: Distribution to build (``sdist`` or ``wheel``)
        :param output_directory: Directory to put the built distribution in
        :param config_settings: Config settings for the build backend
        :param metadata_directory: If provided, should be the return value of a
            previous ``prepare`` call on the same ``distribution`` kind
        :returns: The full path to the built distribution
        """
        self.log(f'Building {distribution}...')
        kwargs = {} if metadata_directory is None else {'metadata_directory': metadata_directory}
        return self._call_backend(f'build_{distribution}', output_directory, config_settings, **kwargs)

    def metadata_path(self, output_directory: PathType) -> str:
        """
        Generate the metadata directory of a distribution and return its path.

        If the backend does not support the ``prepare_metadata_for_build_wheel``
        hook, a wheel will be built and the metadata will be extracted from it.

        :param output_directory: Directory to put the metadata distribution in
        :returns: The path of the metadata directory
        """
        # prepare_metadata hook
        metadata = self.prepare('wheel', output_directory)
        if metadata is not None:
            return metadata

        # fallback to build_wheel hook
        wheel = self.build('wheel', output_directory)
        match = _WHEEL_NAME_REGEX.match(os.path.basename(wheel))
        if not match:
            raise ValueError('Invalid wheel')
        distinfo = f"{match['distribution']}-{match['version']}.dist-info"
        member_prefix = f'{distinfo}/'
        with zipfile.ZipFile(wheel) as w:
            w.extractall(
                output_directory,
                (member for member in w.namelist() if member.startswith(member_prefix)),
            )
        return os.path.join(output_directory, distinfo)

    def _call_backend(
        self, hook_name: str, outdir: PathType, config_settings: Optional[ConfigSettingsType] = None, **kwargs: Any
    ) -> str:
        outdir = os.path.abspath(outdir)

        callback = getattr(self._hook, hook_name)

        if os.path.exists(outdir):
            if not os.path.isdir(outdir):
                raise BuildException(f"Build path '{outdir}' exists and is not a directory")
        else:
            os.makedirs(outdir)

        with self._handle_backend(hook_name):
            basename: str = callback(outdir, config_settings, **kwargs)

        return os.path.join(outdir, basename)

    @contextlib.contextmanager
    def _handle_backend(self, hook: str) -> Iterator[None]:
        with _working_directory(self.srcdir):
            try:
                yield
            except pep517.wrappers.BackendUnavailable as exception:
                raise BuildBackendException(
                    exception,
                    f"Backend '{self._backend}' is not available.",
                    sys.exc_info(),
                )
            except subprocess.CalledProcessError as exception:
                raise BuildBackendException(exception, f'Backend subprocess exited when trying to invoke {hook}')
            except Exception as exception:
                raise BuildBackendException(exception, exc_info=sys.exc_info())

    @staticmethod
    def log(message: str) -> None:
        """
        Log a message.

        The default implementation uses the logging module but this function can be
        overridden by users to have a different implementation.

        :param message: Message to output
        """
        if sys.version_info >= (3, 8):
            _logger.log(logging.INFO, message, stacklevel=2)
        else:
            _logger.log(logging.INFO, message)


__all__ = [
    '__version__',
    'BuildBackendException',
    'BuildException',
    'ConfigSettingsType',
    'FailedProcessError',
    'ProjectBuilder',
    'RunnerType',
    'TypoWarning',
    'check_dependency',
]


def __dir__() -> List[str]:
    return __all__
