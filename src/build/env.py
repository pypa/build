import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import types
from typing import Dict, Iterable, List, Optional, Sequence, Type, cast

if sys.version_info[0] == 2:
    FileExistsError = OSError

try:
    import pip
except ImportError:  # pragma: no cover
    pip = None  # pragma: no cover

_HAS_SYMLINK = None  # type: Optional[bool]


def _fs_supports_symlink():  # type: () -> bool
    if not hasattr(os, 'symlink'):
        return False

    if sys.platform.startswith(('aix', 'darwin', 'freebsd', 'linux')):
        return True
    else:
        with tempfile.NamedTemporaryFile(prefix='TmP') as tmp_file:
            temp_dir = os.path.dirname(tmp_file.name)
            dest = os.path.join(temp_dir, '{}-{}'.format(tmp_file.name, 'b'))
            try:
                os.symlink(tmp_file.name, dest)
                return True
            except (OSError, NotImplementedError):
                return False


def fs_supports_symlink():  # type: () -> bool
    global _HAS_SYMLINK
    if _HAS_SYMLINK is None:
        _HAS_SYMLINK = _fs_supports_symlink()
    return _HAS_SYMLINK


class IsolatedEnvironment(object):
    """
    Isolated build environment context manager

    Non-standard paths injected directly to sys.path still be passed to the environment.
    """

    _MANIPULATE_PATHS = ('purelib', 'platlib')

    def __init__(self, remove_paths, _executable=sys.executable):  # type: (Sequence[str], str) -> None
        """
        :param remove_paths: Import paths that should be removed from the environment
        """
        self._env = {}  # type: Dict[str, Optional[str]]
        self._env_vars = {}  # type: Dict[str, str]
        self._path = None  # type: Optional[str]
        self._remove_paths = []  # type: List[str]
        self._executable = _executable
        self._old_executable = None  # type: Optional[str]
        self._pip_executable = None  # type: Optional[str]

        # normalize paths so that we can compare them -- required on case insensitive systems
        for path in remove_paths:
            self._remove_paths.append(os.path.normcase(path))

    @property
    def path(self):  # type: () -> str
        if not self._path:
            raise RuntimeError("{} context environment hasn't been entered yet".format(self.__class__.__name__))

        return self._path

    @property
    def executable(self):  # type: () -> str
        return self._executable

    @classmethod
    def for_current(cls):  # type: () -> IsolatedEnvironment
        """
        Creates an isolated environment for the current interpreter
        """
        remove_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
        # also remove the pth file adding this project (when installed via --develop install)
        for path in sys.path:
            if os.path.exists(os.path.join(path, 'build.egg-info')):
                remove_paths.append(path)  # pragma: no cover

        return cls(remove_paths)

    def _replace_env(self, key, new):  # type: (str, Optional[str]) -> None
        """
        Replaces an environment variable
        """
        if not new:  # pragma: no cover
            return

        self._env[key] = os.environ.get(key, None)
        os.environ[key] = new

    def _pop_env(self, key):  # type: (str) -> None
        """
        Removes an environment variable
        """
        self._env[key] = os.environ.pop(key, None)

    def _restore_env(self):  # type: () -> None
        """
        Restores the initial environment variables
        """
        for key, val in self._env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def _get_env_path(self, path):  # type: (str) -> Optional[str]
        """
        Returns sysconfig path from our environment
        """
        return sysconfig.get_path(path, vars=self._env_vars)

    def _create_env_venv(self):  # type: () -> None
        import venv

        venv.EnvBuilder(with_pip=False).create(self.path)

        env_scripts = self._get_env_path('scripts')
        if not env_scripts:
            raise RuntimeError("Couldn't get environment scripts path")
        exe = 'pypy3' if platform.python_implementation() == 'PyPy' else 'python'
        if os.name == 'nt':
            exe = '{}.exe'.format(exe)

        self._executable = os.path.join(self.path, env_scripts, exe)
        if not os.path.exists(self._executable):
            raise RuntimeError('Virtual environment creation failed, executable {} missing'.format(self._executable))

        # Scenario 1: pip is available (either installed or via pth file) within the python executable alongside
        # this projects environment: in this case we should be able to import it
        if pip is not None:
            self._pip_executable = sys.executable
            return
        # Scenario 2: this project is installed into a virtual environment that has no pip, but the matching system has
        # Scenario 3: there's a pip executable on PATH
        # Scenario 4: no pip can be found, we might be able to provision one into the isolated build env via ensurepip
        cmd = [self.executable, '-Im', 'ensurepip', '--upgrade', '--default-pip']
        try:
            subprocess.check_call(cmd, cwd=self.path)
        except subprocess.CalledProcessError:  # pragma: no cover
            pass  # pragma: no cover
        # avoid the setuptools from ensurepip to break the isolation
        subprocess.check_call([self.executable, '-Im', 'pip', 'uninstall', 'setuptools', '-y'])
        self._pip_executable = self.executable

    def _create_env_virtualenv(self):  # type: () -> None
        from virtualenv import cli_run

        cmd = [str(self.path), '--no-setuptools', '--no-wheel', '--activators', '']
        if pip is not None:
            cmd.append('--no-pip')
        result = cli_run(cmd, setup_logging=False)
        self._executable = str(result.creator.exe)
        self._pip_executable = self._executable
        if pip is not None:
            self._pip_executable = sys.executable

    def _create_isolated_env(self):  # type: () -> None
        if sys.version_info[0] == 2:
            self._create_env_virtualenv()

        else:
            self._create_env_venv()

    def __enter__(self):  # type: () -> IsolatedEnvironment
        """
        Set up the environment

        The environment path should be empty
        """
        self._path = tempfile.mkdtemp(prefix='build-env-')
        self._env_vars = {
            'base': self.path,
            'platbase': self.path,
        }

        self._create_isolated_env()

        self._pop_env('PIP_REQUIRE_VIRTUALENV')
        # address https://github.com/pypa/pep517/pull/93
        self._old_executable, sys.executable = sys.executable, self._executable

        return self

    def __exit__(self, typ, value, traceback):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[types.TracebackType]) -> None
        """
        Restores the everything to the original state
        """
        if self._old_executable is not None:
            sys.executable = self._old_executable
        if self.path and os.path.isdir(self.path):
            shutil.rmtree(self.path)

        self._restore_env()

    def install(self, requirements):  # type: (Iterable[str]) -> None
        """
        Installs the specified PEP 508 requirements on the environment

        Passing non PEP 508 strings will result in undefined behavior, you
        *should not* rely on it. It is merely an implementation detail, it may
        change any time without warning.
        """
        if not requirements:
            return

        with tempfile.NamedTemporaryFile('w+', prefix='build-reqs-', suffix='.txt', delete=False) as req_file:
            req_file.write(os.linesep.join(requirements))
            req_file.close()
            cmd = [
                cast(str, self._pip_executable),
                # on python2 if isolation is achieved via environment variables, we need to ignore those while calling
                # host python (otherwise pip would not be available within it)
                '-{}m'.format('E' if self._pip_executable == self._executable and sys.version_info[0] == 2 else ''),
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
            os.unlink(req_file.name)
