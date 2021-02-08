"""
Creates and manages isolated build environments.
"""
import abc
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import tempfile

from types import TracebackType
from typing import Iterable, Optional, Tuple, Type

from ._compat import abstractproperty, add_metaclass


try:
    import virtualenv
except ImportError:  # pragma: no cover
    virtualenv = None  # pragma: no cover


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

    def __init__(self):  # type: () -> None
        self._path = None  # type: Optional[str]

    def __enter__(self):  # type: () -> IsolatedEnv
        """
        Create an isolated build environment.

        :return: The isolated build environment
        """
        self._path = tempfile.mkdtemp(prefix='build-env-')
        try:
            # use virtualenv on Python 2 (no stdlib venv) or when virtualenv is available (as it's faster than venv)
            if sys.version_info[0] == 2 or virtualenv is not None:
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


def _create_isolated_env_venv(path):  # type: (str) -> Tuple[str, str]
    """
    On Python 3 we use the venv package from the standard library.

    :param path: The path where to create the isolated build environment
    :return: The Python executable and script folder
    """
    import venv

    venv.EnvBuilder(with_pip=True).create(path)
    executable, script_dir = _find_executable_and_scripts(path)
    # avoid the setuptools from ensurepip to break the isolation
    if sys.version_info < (3, 6, 6):  # python 3.5 up to 3.6.5 come with pip 9 that's too old, for new standards
        subprocess.check_call([executable, '-m', 'pip', 'install', '-U', 'pip'])
    subprocess.check_call([executable, '-m', 'pip', 'uninstall', 'setuptools', '-y'])
    return executable, script_dir


def _find_executable_and_scripts(path):  # type: (str) -> Tuple[str, str]
    """
    Detect the Python executable and script folder of a virtual environment.

    :param path: The location of the virtual environment
    :return: The Python executable and script folder
    """
    config_vars = sysconfig.get_config_vars().copy()  # globally cached, copy before altering it
    config_vars['base'] = path
    env_scripts = sysconfig.get_path('scripts', vars=config_vars)
    if not env_scripts:
        raise RuntimeError("Couldn't get environment scripts path")
    exe = 'pypy3' if platform.python_implementation() == 'PyPy' else 'python'
    if os.name == 'nt':
        exe = '{}.exe'.format(exe)
    executable = os.path.join(env_scripts, exe)
    if not os.path.exists(executable):
        raise RuntimeError('Virtual environment creation failed, executable {} missing'.format(executable))
    return executable, env_scripts


__all__ = (
    'IsolatedEnvBuilder',
    'IsolatedEnv',
)
