# SPDX-License-Identifier: MIT

"""
build - A simple, correct PEP 517 package builder
"""
__version__ = '0.3.0'

import contextlib
import difflib
import os
import sys
import warnings

from collections import OrderedDict
from typing import AbstractSet, Any, Callable, Dict, Iterator, Mapping, Optional, Sequence, Set, Text, Tuple, Union

import pep517.wrappers
import toml
import toml.decoder


if sys.version_info < (3,):
    FileNotFoundError = IOError
    PermissionError = OSError


ConfigSettings = Mapping[str, Union[str, Sequence[str]]]


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

    def __init__(self, exception):  # type: (Exception) -> None
        super(BuildBackendException, self).__init__()
        self.exception = exception  # type: Exception

    def __str__(self):  # type: () -> str
        return 'Backend operation failed: {!r}'.format(self.exception)


class TypoWarning(Warning):
    """
    Warning raised when a potential typo is found
    """


def check_dependency(req_string, ancestral_req_strings=(), parent_extras=frozenset()):
    # type: (str, Tuple[str, ...], AbstractSet[str]) -> Iterator[Tuple[str, ...]]
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


def _find_typo(dictionary, expected):  # type: (Mapping[str, str], str) -> None
    if expected not in dictionary:
        for obj in dictionary:
            if difflib.SequenceMatcher(None, expected, obj).ratio() >= 0.8:
                warnings.warn(
                    "Found '{}' in pyproject.toml, did you mean '{}'?".format(obj, expected),
                    TypoWarning,
                )


@contextlib.contextmanager
def _working_directory(path):  # type: (str) -> Iterator[None]
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

    def __init__(self, srcdir, python_executable=sys.executable, scripts_dir=None):
        # type: (str, Union[bytes, Text], Optional[Union[bytes, Text]]) -> None
        """
        :param srcdir: The source directory
        :param scripts_dir: The location of the scripts dir (defaults to the folder where the python executable lives)
        :param python_executable: The python executable where the backend lives
        """
        self.srcdir = os.path.abspath(srcdir)  # type: str

        spec_file = os.path.join(srcdir, 'pyproject.toml')

        try:
            with open(spec_file) as f:
                spec = toml.load(f)
        except FileNotFoundError:
            spec = {}
        except PermissionError as e:
            raise BuildException("{}: '{}' ".format(e.strerror, e.filename))
        except toml.decoder.TomlDecodeError as e:
            raise BuildException('Failed to parse {}: {} '.format(spec_file, e))

        build_system = spec.get('build-system')
        # if pyproject.toml is missing (per PEP 517) or [build-system] is missing (per PEP 518),
        # use default values.
        if build_system is None:
            _find_typo(spec, 'build-system')
            build_system = _DEFAULT_BACKEND
        # if [build-system] is present, it must have a ``requires`` field (per PEP 518).
        elif 'requires' not in build_system:
            _find_typo(build_system, 'requires')
            raise BuildException("Missing 'build-system.requires' in {}".format(spec_file))
        # if ``build-backend`` is missing, inject the legacy setuptools backend
        # but leave ``requires`` alone to emulate pip.
        elif 'build-backend' not in build_system:
            _find_typo(build_system, 'build-backend')
            build_system['build-backend'] = _DEFAULT_BACKEND['build-backend']

        self._build_system = build_system
        self._backend = self._build_system['build-backend']
        self._scripts_dir = scripts_dir
        self._hook = pep517.wrappers.Pep517HookCaller(
            self.srcdir,
            self._backend,
            backend_path=self._build_system.get('backend-path'),
            python_executable=python_executable,
            runner=self._runner,
        )

    def _runner(self, cmd, cwd=None, extra_environ=None):
        # type: (Sequence[str], Optional[Union[bytes, Text]], Optional[Dict[str, str]]) -> None
        # if script dir is specified must be inserted at the start of PATH (avoid duplicate path while doing so)
        if self.scripts_dir is not None:
            paths = OrderedDict()  # type:  Dict[str, None]
            paths[str(self.scripts_dir)] = None
            if 'PATH' in os.environ:
                paths.update((i, None) for i in os.environ['PATH'].split(os.pathsep))
            extra_environ = {} if extra_environ is None else extra_environ
            extra_environ['PATH'] = os.pathsep.join(paths)
        pep517.default_subprocess_runner(cmd, cwd, extra_environ)

    @property
    def python_executable(self):  # type: () -> Union[bytes, Text]
        """
        The Python executable used to invoke the backend.
        """
        # make mypy happy
        exe = self._hook.python_executable  # type: Union[bytes, Text]
        return exe

    @python_executable.setter
    def python_executable(self, value):  # type: (Union[bytes, Text]) -> None
        self._hook.python_executable = value

    @property
    def scripts_dir(self):  # type: () -> Union[None, bytes, Text]
        """
        The folder where the scripts are stored for the python executable.
        """
        return self._scripts_dir

    @scripts_dir.setter
    def scripts_dir(self, value):  # type: (Union[None, bytes, Text]) -> None
        self._scripts_dir = value

    @property
    def build_dependencies(self):  # type: () -> Set[str]
        """
        The dependencies defined in the ``pyproject.toml``'s
        ``build-system.requires`` field or the default build dependencies
        if ``pyproject.toml`` is missing or ``build-system`` is undefined.
        """
        return set(self._build_system['requires'])

    def get_dependencies(self, distribution, config_settings=None):  # type: (str, Optional[ConfigSettings]) -> Set[str]
        """
        Return the dependencies defined by the backend in addition to
        :attr:`build_dependencies` for a given distribution.

        :param distribution: Distribution to get the dependencies of
            (``sdist`` or ``wheel``)
        :param config_settings: Config settings for the build backend
        """
        get_requires = getattr(self._hook, 'get_requires_for_build_{}'.format(distribution))

        try:
            with _working_directory(self.srcdir):
                return set(get_requires(config_settings))
        except pep517.wrappers.BackendUnavailable:
            raise BuildException("Backend '{}' is not available.".format(self._backend))
        except Exception as e:
            raise BuildBackendException(e)

    def check_dependencies(self, distribution, config_settings=None):
        # type: (str, Optional[ConfigSettings]) -> Set[Tuple[str, ...]]
        """
        Return the dependencies which are not satisfied from the combined set of
        :attr:`build_dependencies` and :meth:`get_dependencies` for a given
        distribution.

        :param distribution: Distribution to check (``sdist`` or ``wheel``)
        :param config_settings: Config settings for the build backend
        :returns: Set of variable-length unmet dependency tuples
        """
        dependencies = self.get_dependencies(distribution, config_settings).union(self.build_dependencies)
        return {u for d in dependencies for u in check_dependency(d)}

    def prepare(self, distribution, output_directory, config_settings=None):
        # type: (str, str, Optional[ConfigSettings]) -> Optional[str]
        """
        Prepare metadata for a distribution.

        :param distribution: Distribution to build (must be ``wheel``)
        :param output_directory: Directory to put the prepared metadata in
        :param config_settings: Config settings for the build backend
        :returns: The full path to the prepared metadata directory
        """
        prepare = getattr(self._hook, 'prepare_metadata_for_build_{}'.format(distribution))
        try:
            return self._call_backend(prepare, output_directory, config_settings, _allow_fallback=False)
        except BuildBackendException as exception:
            if isinstance(exception.exception, pep517.wrappers.HookMissing):
                return None
            raise

    def build(self, distribution, output_directory, config_settings=None, metadata_directory=None):
        # type: (str, str, Optional[ConfigSettings], Optional[str]) -> str
        """
        Build a distribution.

        :param distribution: Distribution to build (``sdist`` or ``wheel``)
        :param output_directory: Directory to put the built distribution in
        :param config_settings: Config settings for the build backend
        :param metadata_directory: If provided, should be the return value of a
            previous ``prepare`` call on the same ``distribution`` kind
        :returns: The full path to the built distribution
        """
        build = getattr(self._hook, 'build_{}'.format(distribution))
        kwargs = {} if metadata_directory is None else {'metadata_directory': metadata_directory}
        return self._call_backend(build, output_directory, config_settings, **kwargs)

    def _call_backend(self, callback, outdir, config_settings=None, **kwargs):
        # type: (Callable[...,str], str, Optional[ConfigSettings], Any) -> str
        outdir = os.path.abspath(outdir)

        if os.path.exists(outdir):
            if not os.path.isdir(outdir):
                raise BuildException("Build path '{}' exists and is not a directory".format(outdir))
        else:
            os.mkdir(outdir)

        try:
            with _working_directory(self.srcdir):
                basename = callback(outdir, config_settings, **kwargs)  # type: str
                return os.path.join(outdir, basename)
        except pep517.wrappers.BackendUnavailable:
            raise BuildException("Backend '{}' is not available.".format(self._backend))
        except Exception as exception:
            raise BuildBackendException(exception)


__all__ = (
    '__version__',
    'ConfigSettings',
    'BuildException',
    'BuildBackendException',
    'TypoWarning',
    'check_dependency',
    'ProjectBuilder',
)
