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
    import pip
except ImportError:  # pragma: no cover
    pip = None  # pragma: no cover


@add_metaclass(abc.ABCMeta)
class IsolatedEnv(object):
    """Abstract base of isolated build environments, as required by the build project."""

    @abstractproperty
    def executable(self):  # type: () -> str
        """Return the executable of the isolated build environment."""
        raise NotImplementedError

    @abc.abstractmethod
    def install(self, requirements):  # type: (Iterable[str]) -> None
        """
        Install PEP-508 requirements into the isolated build environment.

        :param requirements: PEP-508 requirements
        """
        raise NotImplementedError


class IsolatedEnvBuilder(object):
    def __init__(self):  # type: () -> None
        """Builder object for isolated environment."""
        self._path = None  # type: Optional[str]

    def __enter__(self):  # type: () -> IsolatedEnv
        """
        Creates an isolated build environment.

        :return: the isolated build environment
        """
        self._path = tempfile.mkdtemp(prefix='build-env-')
        try:
            executable, pip_executable = _create_isolated_env(self._path)
            return _IsolatedEnvVenvPip(path=self._path, python_executable=executable, pip_executable=pip_executable)
        except Exception:  # cleanup folder if creation fails
            self.__exit__(*sys.exc_info())
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
        """
        Delete the created isolated build environment.

        :param exc_type: the type of exception raised (if any)
        :param exc_val: the value of exception raised (if any)
        :param exc_tb: the traceback of exception raised (if any)
        """
        if self._path is not None and os.path.exists(self._path):  # in case the user already deleted skip remove
            shutil.rmtree(self._path)


class _IsolatedEnvVenvPip(IsolatedEnv):
    """
    Isolated build environment context manager

    Non-standard paths injected directly to sys.path still be passed to the environment.
    """

    def __init__(self, path, python_executable, pip_executable):
        # type: (str, str, str) -> None
        """
        Define an isolated build environment.

        :param path: the path where the environment exists
        :param python_executable: the python executable within the environment
        :param pip_executable: an executable that allows installing packages within the environment
        """
        self._path = path
        self._pip_executable = pip_executable
        self._python_executable = python_executable

    @property
    def path(self):  # type: () -> str
        """:return: the location of the isolated build environment"""
        return self._path

    @property
    def executable(self):  # type: () -> str
        """:return: the python executable of the isolated build environment"""
        return self._python_executable

    def install(self, requirements):  # type: (Iterable[str]) -> None
        """
        Installs the specified PEP 508 requirements on the environment

        :param requirements: PEP-508 requirement specification to install

        :note: Passing non PEP 508 strings will result in undefined behavior, you *should not* rely on it. It is \
               merely an implementation detail, it may change any time without warning.
        """
        if not requirements:
            return

        with tempfile.NamedTemporaryFile('w+', prefix='build-reqs-', suffix='.txt', delete=False) as req_file:
            req_file.write(os.linesep.join(requirements))
        try:
            cmd = [
                self._pip_executable,
                # on python2 if isolation is achieved via environment variables, we need to ignore those while calling
                # host python (otherwise pip would not be available within it)
                '-{}m'.format('E' if self._pip_executable == self.executable and sys.version_info[0] == 2 else ''),
                'pip',
                'install',
                '--prefix',
                self.path,
                '--ignore-installed',
                '--no-warn-script-location',
                '-r',
                os.path.abspath(req_file.name),
            ]
            subprocess.check_call(cmd)
        finally:
            os.unlink(req_file.name)


if sys.version_info[0] == 2:  # noqa: C901 # disable if too complex

    def _create_isolated_env(path):  # type: (str) -> Tuple[str, str]
        """
        On Python 2 we use the virtualenv package to provision a virtual environment.

        :param path: the folder where to create the isolated build environment
        :return: the isolated build environment executable, and the pip to use to install packages into it
        """
        from virtualenv import cli_run

        cmd = [str(path), '--no-setuptools', '--no-wheel', '--activators', '']
        if pip is not None:
            cmd.append('--no-pip')
        result = cli_run(cmd, setup_logging=False)
        executable = str(result.creator.exe)
        pip_executable = executable if pip is None else sys.executable
        return executable, pip_executable


else:

    def _create_isolated_env(path):  # type: (str) -> Tuple[str, str]
        """
        On Python 3 we use the venv package from the standard library, and if host python has no pip the ensurepip
        package to provision one into the created virtual environment.

        :param path: the folder where to create the isolated build environment
        :return: the isolated build environment executable, and the pip to use to install packages into it
        """
        import venv

        venv.EnvBuilder(with_pip=False).create(path)
        executable = _find_executable(path)

        # Scenario 1: pip is available (either installed or via pth file) within the python executable alongside
        # this projects environment: in this case we should be able to import it
        if pip is not None:
            pip_executable = sys.executable
        else:
            # Scenario 2: this project is installed into a virtual environment that has no pip, but the system has
            # Scenario 3: there's a pip executable on PATH
            # Scenario 4: no pip can be found, we might be able to provision one into the build env via ensurepip
            cmd = [executable, '-Im', 'ensurepip', '--upgrade', '--default-pip']
            try:
                subprocess.check_call(cmd, cwd=path)
            except subprocess.CalledProcessError:  # pragma: no cover
                pass  # pragma: no cover
            # avoid the setuptools from ensurepip to break the isolation
            subprocess.check_call([executable, '-Im', 'pip', 'uninstall', 'setuptools', '-y'])
            pip_executable = executable
        return executable, pip_executable

    def _find_executable(path):  # type: (str) -> str
        """
        Detect the executable within a virtual environment.

        :param path: the location of the virtual environment
        :return: the python executable
        """
        config_vars = sysconfig.get_config_vars().copy()  # globally cached, copy before altering it
        config_vars['base'] = path
        env_scripts = sysconfig.get_path('scripts', vars=config_vars)
        if not env_scripts:
            raise RuntimeError("Couldn't get environment scripts path")
        exe = 'pypy3' if platform.python_implementation() == 'PyPy' else 'python'
        if os.name == 'nt':
            exe = '{}.exe'.format(exe)
        executable = os.path.join(path, env_scripts, exe)
        if not os.path.exists(executable):
            raise RuntimeError('Virtual environment creation failed, executable {} missing'.format(executable))
        return executable


__all__ = (
    'IsolatedEnvBuilder',
    'IsolatedEnv',
)
