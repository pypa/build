"""
Creates and manages isolated build environments.
"""
import abc
import functools
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import tempfile

from types import TracebackType
from typing import Iterable, Optional, Tuple, Type

import packaging.requirements
import packaging.version

import build

from ._compat import abstractproperty, add_metaclass


if sys.version_info < (3, 8):
    import importlib_metadata as metadata
else:
    from importlib import metadata

try:
    import virtualenv
except ImportError:
    virtualenv = None


@add_metaclass(abc.ABCMeta)
class IsolatedEnv(object):
    """Abstract base of isolated build environments, as required by the build project."""

    @abstractproperty
    def executable(self):  # type: () -> str
        """The executable of the isolated build environment."""
        raise NotImplementedError

    @abstractproperty
    def scripts_dir(self):  # type: () -> str
        """The scripts directory of the isolated build environment."""
        raise NotImplementedError

    @abc.abstractmethod
    def install(self, requirements):  # type: (Iterable[str]) -> None
        """
        Install packages from PEP 508 requirements in the isolated build environment.

        :param requirements: PEP 508 requirements
        """
        raise NotImplementedError


class IsolatedEnvBuilder(object):
    """Builder object for isolated environments."""

    _has_virtualenv = None  # type: Optional[bool]

    def __init__(self):  # type: () -> None
        self._path = None  # type: Optional[str]

    def _should_use_virtualenv(self):  # type: () -> Optional[bool]
        # virtualenv might be incompatible if it was installed separately
        # from build. This verifies that virtualenv and all of its
        # dependencies are installed as specified by build.
        if self._has_virtualenv is None:
            self.__class__._has_virtualenv = virtualenv is not None and not any(
                packaging.requirements.Requirement(d[1]).name == 'virtualenv'
                for d in build.check_dependency('build[virtualenv]')
                if len(d) > 1
            )
        return self._has_virtualenv

    def __enter__(self):  # type: () -> IsolatedEnv
        """
        Create an isolated build environment.

        :return: The isolated build environment
        """
        self._path = tempfile.mkdtemp(prefix='build-env-')
        try:
            # use virtualenv on Python 2 or when valid virtualenv is available (as it's faster than venv)
            if sys.version_info < (3,) or self._should_use_virtualenv():
                executable, scripts_dir = _create_isolated_env_virtualenv(self._path)
            else:
                executable, scripts_dir = _create_isolated_env_venv(self._path)
            return _IsolatedEnvVenvPip(path=self._path, python_executable=executable, scripts_dir=scripts_dir)
        except Exception:  # cleanup folder if creation fails
            self.__exit__(*sys.exc_info())
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
        """
        Delete the created isolated build environment.

        :param exc_type: The type of exception raised (if any)
        :param exc_val: The value of exception raised (if any)
        :param exc_tb: The traceback of exception raised (if any)
        """
        if self._path is not None and os.path.exists(self._path):  # in case the user already deleted skip remove
            shutil.rmtree(self._path)


class _IsolatedEnvVenvPip(IsolatedEnv):
    """
    Isolated build environment context manager

    Non-standard paths injected directly to sys.path will still be passed to the environment.
    """

    def __init__(self, path, python_executable, scripts_dir):
        # type: (str, str, str) -> None
        """
        :param path: The path where the environment exists
        :param python_executable: The python executable within the environment
        """
        self._path = path
        self._python_executable = python_executable
        self._scripts_dir = scripts_dir

    @property
    def path(self):  # type: () -> str
        """The location of the isolated build environment."""
        return self._path

    @property
    def executable(self):  # type: () -> str
        """The python executable of the isolated build environment."""
        return self._python_executable

    @property
    def scripts_dir(self):  # type: () -> str
        return self._scripts_dir

    def install(self, requirements):  # type: (Iterable[str]) -> None
        """
        Install packages from PEP 508 requirements in the isolated build environment.

        :param requirements: PEP 508 requirement specification to install

        :note: Passing non-PEP 508 strings will result in undefined behavior, you *should not* rely on it. It is
               merely an implementation detail, it may change any time without warning.
        """
        if not requirements:
            return

        # pip does not honour environment markers in command line arguments
        # but it does for requirements from a file
        with tempfile.NamedTemporaryFile('w+', prefix='build-reqs-', suffix='.txt', delete=False) as req_file:
            req_file.write(os.linesep.join(requirements))
        try:
            cmd = [
                self.executable,
                '-{}m'.format('E' if sys.version_info[0] == 2 else 'I'),
                'pip',
                'install',
                '--use-pep517',
                '--no-warn-script-location',
                '-r',
                os.path.abspath(req_file.name),
            ]
            subprocess.check_call(cmd)
        finally:
            os.unlink(req_file.name)


def _create_isolated_env_virtualenv(path):  # type: (str) -> Tuple[str, str]
    """
    On Python 2 we use the virtualenv package to provision a virtual environment.

    :param path: The path where to create the isolated build environment
    :return: The Python executable and script folder
    """
    cmd = [str(path), '--no-setuptools', '--no-wheel', '--activators', '']
    result = virtualenv.cli_run(cmd, setup_logging=False)
    executable = str(result.creator.exe)
    script_dir = str(result.creator.script_dir)
    return executable, script_dir


# venv only exists on Python 3+
if sys.version_info >= (3,):  # noqa: C901

    @functools.lru_cache(maxsize=None)
    def _fs_supports_symlink():  # type: () -> bool
        """Return True if symlinks are supported"""
        # Using definition used by venv.main()
        if os.name != 'nt':
            return True

        # Windows may support symlinks (setting in Windows 10)
        with tempfile.NamedTemporaryFile(prefix='build-symlink-') as tmp_file:
            dest = '{}-b'.format(tmp_file)
            try:
                os.symlink(tmp_file.name, dest)
                os.unlink(dest)
                return True
            except (OSError, NotImplementedError, AttributeError):
                return False

    def _create_isolated_env_venv(path):  # type: (str) -> Tuple[str, str]
        """
        On Python 3 we use the venv package from the standard library.

        :param path: The path where to create the isolated build environment
        :return: The Python executable and script folder
        """
        import venv

        venv.EnvBuilder(with_pip=True, symlinks=_fs_supports_symlink()).create(path)
        executable, script_dir, purelib = _find_executable_and_scripts(path)

        # Get the version of pip in the environment
        pip_distribution = next(iter(metadata.distributions(name='pip', path=[purelib])))
        current_pip_version = packaging.version.Version(pip_distribution.version)

        if platform.system() == 'Darwin' and int(platform.mac_ver()[0].split('.')[0]) >= 11:
            # macOS 11+ name scheme change requires 20.3. Intel macOS 11.0 can be told to report 10.16 for backwards
            # compatibility; but that also fixes earlier versions of pip so this is only needed for 11+.
            is_apple_silicon_python = sys.version_info >= (3, 6) and platform.machine() != 'x86_64'
            minimum_pip_version = '21.0.1' if is_apple_silicon_python else '20.3.0'
        else:
            # PEP-517 and manylinux1 was first implemented in 19.1
            minimum_pip_version = '19.1.0'

        if current_pip_version < packaging.version.Version(minimum_pip_version):
            subprocess.check_call([executable, '-m', 'pip', 'install', 'pip>={}'.format(minimum_pip_version)])

        # Avoid the setuptools from ensurepip to break the isolation
        subprocess.check_call([executable, '-m', 'pip', 'uninstall', 'setuptools', '-y'])
        return executable, script_dir

    def _find_executable_and_scripts(path):  # type: (str) -> Tuple[str, str, str]
        """
        Detect the Python executable and script folder of a virtual environment.

        :param path: The location of the virtual environment
        :return: The Python executable, script folder, and purelib folder
        """
        config_vars = sysconfig.get_config_vars().copy()  # globally cached, copy before altering it
        config_vars['base'] = path
        # The Python that ships with the macOS developer tools varies the
        # default scheme depending on whether the ``sys.prefix`` is part of a framework.
        # The framework "osx_framework_library" scheme
        # can't be used to expand the paths in a venv, which
        # can happen if build itself is not installed in a venv.
        # If the Apple-custom "osx_framework_library" scheme is available
        # we enforce "posix_prefix", the venv scheme, for isolated envs.
        if 'osx_framework_library' in sysconfig.get_scheme_names():
            paths = sysconfig.get_paths(scheme='posix_prefix', vars=config_vars)
        else:
            paths = sysconfig.get_paths(vars=config_vars)
        executable = os.path.join(paths['scripts'], 'python.exe' if os.name == 'nt' else 'python')
        if not os.path.exists(executable):
            raise RuntimeError('Virtual environment creation failed, executable {} missing'.format(executable))

        return executable, paths['scripts'], paths['purelib']


__all__ = (
    'IsolatedEnvBuilder',
    'IsolatedEnv',
)
