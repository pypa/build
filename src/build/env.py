import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import types
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Type

if sys.version_info[0] == 2:  # pragma: no cover
    FileExistsError = OSError

_HAS_SYMLINK = None  # type: Optional[bool]


DARWIN_CACHE = '~/Library/Caches/pypa/build'
WINDOWS_CACHE = '~\\AppData\\Local\\pypa\\build\\Cache'
LINUX_CACHE = '~/.cache/pypa/build'


def get_shared_folder():
    return DARWIN_CACHE if sys.platform == 'darwin' else WINDOWS_CACHE if sys.platform == 'win32' else LINUX_CACHE


class Isolation(object):
    def __init__(self, enabled=True, ensure_pip=False, cache=None, reset_cache=False):
        # type: (bool, bool, Optional[str], bool) -> None
        self.enabled = enabled
        self.ensure_pip = ensure_pip
        if cache is None:
            cache = get_shared_folder()
        self.cache = cache
        self.reset_cache = reset_cache

    def __eq__(self, other):  # type: (Any) -> bool
        if type(self) != type(other):
            return False
        left = self.enabled, self.ensure_pip, self.cache, self.reset_cache
        right = (other.enabled, other.ensure_pip, other.cache, other.reset_cache)
        return left == right

    def __ne__(self, other):  # type: (Any) -> bool
        return not self.__eq__(other)

    def __repr__(self):  # type: () -> str
        fmt = '{}(enabled={}, ensure_pip={}, cache={}, reset_cache={})'
        return fmt.format(self.__class__.__name__, self.enabled, self.ensure_pip, self.cache, self.reset_cache)


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

    def __init__(self, remove_paths, isolation, _executable=sys.executable):
        # type: (Sequence[str], Isolation, str) -> None
        """
        :param remove_paths: Import paths that should be removed from the environment
        """
        self._env = {}  # type: Dict[str, Optional[str]]
        self._env_vars = {}  # type: Dict[str, str]
        self._path = None  # type: Optional[str]
        self._remove_paths = []  # type: List[str]
        self._executable = _executable
        self._isolation = isolation
        self._cleanup_path = True
        self._old_sys_executable = None  # type: Optional[str]

        # normalize paths so that we can compare them -- required on case insensitive systems
        for path in remove_paths:
            self._remove_paths.append(os.path.normcase(path))

    @property
    def path(self):  # type: () -> str
        if not self._path:
            raise RuntimeError("{} context environment hasn't been entered yet".format(self.__class__.__name__))

        return self._path

    @path.setter
    def path(self, value):  # type: (str) -> None
        self._path = value
        self._cleanup_path = False

    @property
    def executable(self):  # type: () -> str
        return self._executable

    @classmethod
    def for_current(cls, isolation=None):  # type: (Optional[Isolation]) -> IsolatedEnvironment
        """
        Creates an isolated environment for the current interpreter
        """
        remove_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)

        for path in cls._MANIPULATE_PATHS:
            our_path = sysconfig.get_path(path)
            if our_path:
                remove_paths.append(our_path)

            for scheme in sysconfig.get_scheme_names():
                our_path = sysconfig.get_path(path, scheme)
                if our_path:
                    remove_paths.append(our_path)
        if isolation is None:
            isolation = Isolation(enabled=True, ensure_pip=True)
        return cls(remove_paths, isolation)

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

    def _symlink_relative(self, path):  # type: (Optional[str]) -> None
        """
        Symlinks a path into our environment

        The original prefix will be removed and replaced with our environmenmt's

        If the path is not valid, nothing will happen
        """
        if not path:  # pragma: no cover
            return

        prefix = sysconfig.get_config_var('prefix')
        if prefix and path and path.startswith(prefix):
            new_path = os.path.join(self.path, path[len(prefix + os.pathsep) :])
            if not os.path.exists(new_path):
                try:
                    os.makedirs(os.path.dirname(new_path))
                except FileExistsError:
                    pass
                if fs_supports_symlink():
                    os.symlink(path, new_path)
                else:
                    import shutil

                    shutil.copytree(path, new_path)

    def _create_env_pythonhome(self):  # type: () -> None
        sys_path = sys.path[1:]

        for path in self._MANIPULATE_PATHS:
            env_path = self._get_env_path(path)
            if env_path:
                sys_path.append(os.path.normcase(env_path))

        for path in self._remove_paths:
            if path in sys_path:
                sys_path.remove(path)

        env_scripts = self._get_env_path('scripts')
        if env_scripts is None:  # pragma: no cover
            raise RuntimeError('Missing scripts directory in sysconfig')

        exe_path = [env_scripts]
        if 'PATH' in os.environ:
            exe_path.append(os.environ['PATH'])

        self._replace_env('PATH', os.pathsep.join(exe_path))
        self._replace_env('PYTHONPATH', os.pathsep.join(sys_path))

        # Point the Python interpreter to our environment
        self._replace_env('PYTHONHOME', self.path)

        self._symlink_relative(sysconfig.get_path('include'))
        self._symlink_relative(sysconfig.get_path('platinclude'))
        self._symlink_relative(sysconfig.get_config_var('LIBPL'))

    def _create_env_venv(self):  # type: () -> None
        if sys.version_info[0] == 2:
            raise RuntimeError('venv not available on Python 2')

        import venv

        venv.EnvBuilder(with_pip=False, clear=True).create(self.path)

        env_scripts = self._get_env_path('scripts')
        if not env_scripts:
            raise RuntimeError("Couldn't get environment scripts path")
        exe = 'pypy3' if platform.python_implementation() == 'PyPy' else 'python'
        if os.name == 'nt':
            pythonw = '{}w.exe'.format(exe)
            if (
                os.path.isfile(os.path.join(self.path, env_scripts, pythonw))
                and not
                # pythonw fails on Python 3.5 Windows
                (os.name == 'nt' and sys.version_info[:2] == (3, 5))
            ):
                exe = pythonw
            else:
                exe = '{}.exe'.format(exe)

        self._executable = os.path.join(self.path, env_scripts, exe)
        if not os.path.exists(self._executable):
            raise RuntimeError('Virtual environment creation failed, executable {} missing'.format(self._executable))

    def __enter__(self):  # type: () -> IsolatedEnvironment
        """
        Set up the environment

        The environment path should be empty
        """
        if self._path is None:
            self._path = tempfile.mkdtemp(prefix='build-env-')
        self._env_vars = {
            'base': self.path,
            'platbase': self.path,
        }

        with self._elapsed('Done isolated build environment at {} '.format(self.path)):
            self._create_isolated_python()
            self._provision_pip()

        sys.executable, self._old_sys_executable = self._executable, sys.executable
        self._pop_env('PIP_REQUIRE_VIRTUALENV')

        return self

    @contextmanager
    def _elapsed(self, msg):
        start = datetime.now()
        try:
            yield
        finally:
            print('{} within {}'.format(msg, (datetime.now() - start).total_seconds()))

    def _create_isolated_python(self):
        if sys.version_info[0] == 2:
            self._create_env_pythonhome()
        else:
            self._create_env_venv()

    def _provision_pip(self):
        if self._isolation.ensure_pip:
            subprocess.check_call([self._executable, '-Im', 'ensurepip', '--upgrade', '--default-pip'])
            # we don't want the default setuptools
            subprocess.check_call([self._executable, '-m', 'pip', 'uninstall', 'setuptools', '-y'])
        else:
            # version qualify per python minor, so that we don't break when pip drops older python versions
            folder = os.path.expanduser(os.path.expandvars(self._isolation.cache))
            if self._isolation.reset_cache and os.path.exists(folder):
                print('Delete {}'.format(folder))
                shutil.rmtree(folder)
            try:
                os.makedirs(folder)
            except OSError:  # ignore now and check after to make it parallel safe
                pass
            if not os.path.exists(folder):
                raise RuntimeError('Could not create folder {}'.format(folder))

            # TBD: needs a (file)lock here for parallel safety
            folder = os.path.join(folder, 'pip', '{}.{}'.format(*sys.version_info[0:2]))
            cached_pure_lib = sysconfig.get_path('purelib', vars={'base': folder})
            if not os.path.exists(os.path.join(cached_pure_lib, 'pip')):  # if does not exists yet create one
                env = IsolatedEnvironment.for_current()
                env.path = folder
                with env:
                    pass
            own_pure_lib = sysconfig.get_path('purelib', vars={'base': self._path})
            with open(os.path.join(own_pure_lib, '_pip.pth'), 'wt') as file_handler:
                file_handler.write(cached_pure_lib)

    def __exit__(self, typ, value, traceback):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[types.TracebackType]) -> None
        """
        Restores the everything to the original state
        """
        if self._old_sys_executable is not None:
            sys.executable = self._old_sys_executable
        if self._cleanup_path and self.path and os.path.isdir(self.path):
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
                self.executable,
                '-m',
                'pip',
                'install',
                '--prefix',
                self.path,
                '-r',
                os.path.abspath(req_file.name),
            ]
            with self._elapsed('Done provision build dependencies {}'.format(' '.join(requirements))):
                subprocess.check_call(cmd)
            os.unlink(req_file.name)
