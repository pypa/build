# SPDX-License-Identifier: MIT

"""
build - A simple, correct PEP 517 build frontend
"""

__version__ = '0.7.0'

import contextlib
import difflib
import logging
import os
import re
import subprocess
import sys
import types
import warnings
import zipfile

from typing import TYPE_CHECKING, Any, Dict, Iterator, Mapping, Optional, Set, Tuple, Type, Union

import pep517.wrappers

from . import env
from ._helpers import ConfigSettingsType, PathType, check_dependency, default_runner, rewrap_runner_for_pep517_lib


if TYPE_CHECKING:
    from ._helpers import Distribution, RunnerType, WheelDistribution

try:
    from tomli import TOMLDecodeError
    from tomli import loads as toml_loads
except ModuleNotFoundError:  # pragma: no cover
    from toml import TomlDecodeError as TOMLDecodeError  # type: ignore
    from toml import loads as toml_loads  # type: ignore

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
    Exception raised by :class:`ProjectBuilder`.
    """


class BuildBackendException(Exception):
    """
    Exception raised when a backend operation fails.
    """

    def __init__(
        self, exception: Exception, description: Optional[str] = None, exc_info: _ExcInfoType = (None, None, None)
    ) -> None:
        super().__init__()
        self.exception: Exception = exception
        self.exc_info: _ExcInfoType = exc_info
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


class TypoWarning(Warning):
    """
    Warning raised when a possible typo is found.
    """


@contextlib.contextmanager
def _working_directory(path: str) -> Iterator[None]:
    current = os.getcwd()

    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(current)


def _parse_source_dir(source_dir: PathType) -> str:
    source_dir = os.path.abspath(source_dir)
    if not os.path.isdir(source_dir):
        raise BuildException(f'Source {source_dir} is not a directory')

    pyproject_toml = os.path.join(source_dir, 'pyproject.toml')
    setup_py = os.path.join(source_dir, 'setup.py')
    if not os.path.exists(pyproject_toml) and not os.path.exists(setup_py):
        raise BuildException(f'Source {source_dir} does not appear to be a Python project: no pyproject.toml or setup.py')

    return source_dir


def _load_pyproject_toml(source_dir: PathType) -> Mapping[str, Any]:
    pyproject_toml = os.path.join(source_dir, 'pyproject.toml')
    try:
        with open(pyproject_toml, 'rb') as f:
            return toml_loads(f.read().decode())
    except FileNotFoundError:
        return {}
    except PermissionError as e:
        raise BuildException(f"{e.strerror}: '{e.filename}'")
    except TOMLDecodeError as e:
        raise BuildException(f'Failed to parse {pyproject_toml}: {e}')


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

    _default_rewrapped_runner = staticmethod(rewrap_runner_for_pep517_lib(default_runner))

    def __init__(
        self,
        srcdir: PathType,
        python_executable: str = sys.executable,
        runner: Optional[Union['RunnerType', Tuple['RunnerType', Optional[Mapping[str, str]]]]] = None,
    ) -> None:
        """
        :param srcdir: The project source directory
        :param python_executable: Path of Python executable used to invoke
            PEP 517 hooks
        :param runner: Callback for executing PEP 517 hooks in a subprocess
        """
        self._srcdir = _parse_source_dir(srcdir)
        self._python_executable = python_executable
        self._build_system = _parse_build_system_table(_load_pyproject_toml(self.srcdir))
        self._requires = set(self._build_system['requires'])
        self._backend = self._build_system['build-backend']
        self._hook = pep517.wrappers.Pep517HookCaller(
            self.srcdir,
            self._backend,
            backend_path=self._build_system.get('backend-path'),
            runner=self._default_rewrapped_runner if runner is None else rewrap_runner_for_pep517_lib(runner),
            python_executable=self._python_executable,
        )

    @classmethod
    def from_isolated_env(
        cls,
        isolated_env: 'env.IsolatedEnv',
        srcdir: PathType,
        runner: Optional['RunnerType'] = None,
    ) -> 'ProjectBuilder':
        """
        Instantiate the builder from an isolated environment.

        :param isolated_env: The isolated environment instance
        :param srcdir: The project source directory
        :param runner: Callback for executing PEP 517 hooks in a subprocess
        """
        return cls(
            srcdir,
            python_executable=isolated_env.python_executable,
            runner=(default_runner if runner is None else runner, isolated_env.prepare_environ()),
        )

    @property
    def srcdir(self) -> str:
        """Project source directory."""
        return self._srcdir

    @property
    def python_executable(self) -> str:
        """Path of Python executable used to invoke PEP 517 hooks."""
        return self._python_executable

    @property
    def build_system_requires(self) -> Set[str]:
        """
        The dependencies specified in the project's ``build-system.requires``
        field or the default build dependencies if unspecified.
        """
        return self._requires

    def get_requires_for_build(
        self, distribution: 'Distribution', config_settings: Optional[ConfigSettingsType] = None
    ) -> Set[str]:
        """
        Get the build dependencies requested by the backend for
        a given distribution.

        :param distribution: Distribution to build
        :param config_settings: Config settings passed to the backend
        """
        self.log(f'Getting dependencies for {distribution}...')
        hook_name = f'get_requires_for_build_{distribution}'
        get_requires = getattr(self._hook, hook_name)

        with self._handle_backend(hook_name):
            return set(get_requires(config_settings))

    def check_dependencies(
        self, distribution: 'Distribution', config_settings: Optional[ConfigSettingsType] = None
    ) -> Set[Tuple[str, ...]]:
        """
        Check that the :attr:`build_system_requires` and :meth:`get_requires_for_build`
        dependencies for a given distribution are satisfied and return the dependency
        chain of those which aren't.  The unmet dependency is the last value in the chain.

        :param distribution: Distribution to build
        :param config_settings: Config settings passed to the backend
        :returns: Unmet dependencies in the PEP 508 format
        """
        dependencies = self.get_requires_for_build(distribution, config_settings).union(self.build_system_requires)
        return {u for d in dependencies for u in check_dependency(d)}

    def prepare(
        self,
        distribution: 'WheelDistribution',
        output_directory: PathType,
        config_settings: Optional[ConfigSettingsType] = None,
    ) -> Optional[str]:
        """
        Prepare metadata for a distribution.

        :param distribution: Distribution to build
        :param output_directory: Directory to put the prepared metadata in
        :param config_settings: Config settings passed to the backend
        :returns: The path of the metadata directory
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
        distribution: 'Distribution',
        output_directory: PathType,
        config_settings: Optional[ConfigSettingsType] = None,
        metadata_directory: Optional[str] = None,
    ) -> str:
        """
        Build a distribution.

        :param distribution: Distribution to build
        :param output_directory: Directory to put the built distribution in
        :param config_settings: Config settings passed to the backend
        :param metadata_directory: If provided, should be the return value of a
            previous ``prepare`` call for the same ``distribution`` type
        :returns: The path of the built distribution
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
    'ConfigSettingsType',
    'RunnerType',
    'BuildException',
    'BuildSystemTableValidationError',
    'BuildBackendException',
    'TypoWarning',
    'check_dependency',
    'ProjectBuilder',
]
