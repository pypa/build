# SPDX-License-Identifier: MIT

"""
build - A simple, correct PEP 517 package builder
"""
__version__ = '0.5.1'

import contextlib
import difflib
import io
import os
import re
import subprocess
import sys
import types
import warnings
import zipfile

from collections import OrderedDict
from typing import AbstractSet, Any, Callable, Dict, Iterator, Mapping, Optional, Sequence, Set, Tuple, Type, Union

import pep517.wrappers
import toml


RunnerType = Callable[[Sequence[str], Optional[str], Optional[Mapping[str, str]]], None]
ConfigSettingsType = Mapping[str, Union[str, Sequence[str]]]
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


class BuildException(Exception):
    """
    Exception raised by ProjectBuilder
    """


class BuildBackendException(Exception):
    """
    Exception raised when the backend fails
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


class TypoWarning(Warning):
    """
    Warning raised when a potential typo is found
    """


def _validate_source_directory(srcdir: str) -> None:
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
        dist = importlib_metadata.distribution(req.name)
    except importlib_metadata.PackageNotFoundError:
        # dependency is not installed in the environment.
        yield ancestral_req_strings + (req_string,)
    else:
        if req.specifier and not req.specifier.contains(dist.version, prereleases=True):
            # the installed version is incompatible.
            yield ancestral_req_strings + (req_string,)
        elif dist.requires:
            for other_req_string in dist.requires:
                for unmet_req in check_dependency(other_req_string, ancestral_req_strings + (req_string,), req.extras):
                    # a transitive dependency is not satisfied.
                    yield unmet_req


def _find_typo(dictionary: Mapping[str, str], expected: str) -> None:
    if expected not in dictionary:
        for obj in dictionary:
            if difflib.SequenceMatcher(None, expected, obj).ratio() >= 0.8:
                warnings.warn(
                    f"Found '{obj}' in pyproject.toml, did you mean '{expected}'?",
                    TypoWarning,
                )


@contextlib.contextmanager
def _working_directory(path: str) -> Iterator[None]:
    current = os.getcwd()

    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(current)


class ProjectBuilder(object):
    """
    The PEP 517 consumer API.
    """

    def __init__(
        self,
        srcdir: str,
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
            with io.open(spec_file, encoding='UTF-8') as f:
                spec = toml.load(f)
        except FileNotFoundError:
            spec = {}
        except PermissionError as e:
            raise BuildException(f"{e.strerror}: '{e.filename}' ")
        except toml.TomlDecodeError as e:
            raise BuildException(f'Failed to parse {spec_file}: {e} ')

        build_system = spec.get('build-system')
        # if pyproject.toml is missing (per PEP 517) or [build-system] is missing (per PEP 518),
        # use default values.
        if build_system is None:
            _find_typo(spec, 'build-system')
            build_system = _DEFAULT_BACKEND
        # if [build-system] is present, it must have a ``requires`` field (per PEP 518).
        elif 'requires' not in build_system:
            _find_typo(build_system, 'requires')
            raise BuildException(f"Missing 'build-system.requires' in {spec_file}")
        # if ``build-backend`` is missing, inject the legacy setuptools backend
        # but leave ``requires`` alone to emulate pip.
        elif 'build-backend' not in build_system:
            _find_typo(build_system, 'build-backend')
            build_system['build-backend'] = _DEFAULT_BACKEND['build-backend']

        self._build_system = build_system
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
        self, distribution: str, output_directory: str, config_settings: Optional[ConfigSettingsType] = None
    ) -> Optional[str]:
        """
        Prepare metadata for a distribution.

        :param distribution: Distribution to build (must be ``wheel``)
        :param output_directory: Directory to put the prepared metadata in
        :param config_settings: Config settings for the build backend
        :returns: The full path to the prepared metadata directory
        """
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
        output_directory: str,
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
        kwargs = {} if metadata_directory is None else {'metadata_directory': metadata_directory}
        return self._call_backend(f'build_{distribution}', output_directory, config_settings, **kwargs)

    def metadata_path(self, output_directory: str) -> str:
        """
        Generates the metadata directory of a distribution and returns its path.

        If the backend does not support the ``prepare_metadata_for_build_wheel``
        hook, a wheel will be built and the metadata extracted.

        :param output_directory: Directory to put the metadata distribution in
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
        self, hook_name: str, outdir: str, config_settings: Optional[ConfigSettingsType] = None, **kwargs: Any
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
                raise BuildBackendException(exception, f'Backend subproccess exited when trying to invoke {hook}')
            except Exception as exception:
                raise BuildBackendException(exception, exc_info=sys.exc_info())


__all__ = (
    '__version__',
    'ConfigSettingsType',
    'RunnerType',
    'BuildException',
    'BuildBackendException',
    'TypoWarning',
    'check_dependency',
    'ProjectBuilder',
)
