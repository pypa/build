import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import types


if False:  # TYPE_CHECKING  # pragma: no cover
    from typing import Dict, Optional, Iterable, Sequence, Type


if sys.version_info[0] == 2:  # pragma: no cover
    FileExistsError = OSError


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
    '''
    Isolated build environment context manager

    Non-standard paths injected directly to sys.path still be passed to the environment.
    '''

    MANIPULATE_PATHS = ('purelib', 'platlib')

    def __init__(self, remove_paths):  # type: (Sequence[str]) -> None
        self._env = {}  # type: Dict[str, Optional[str]]
        self._path = None  # type: Optional[str]
        self._remove_paths = remove_paths

    @property
    def path(self):  # type: () -> str
        if not self._path:
            raise RuntimeError("{} context environment hasn't been entered yet".format(self.__class__.__name__))

        return self._path

    @classmethod
    def for_current(cls):  # type: () -> IsolatedEnvironment
        remove_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)

        for path in cls.MANIPULATE_PATHS:
            our_path = sysconfig.get_path(path)
            if our_path:
                remove_paths.append(our_path)

            for scheme in sysconfig.get_scheme_names():
                our_path = sysconfig.get_path(path, scheme)
                if our_path:
                    remove_paths.append(our_path)

        return cls(remove_paths)

    def _replace_env(self, key, new):  # type: (str, Optional[str]) -> None
        if not new:  # pragma: no cover
            return

        self._env[key] = os.environ.get(key, None)
        os.environ[key] = new

    def _restore_env(self):  # type: () -> None
        for key, val in self._env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def _get_env_path(self, path):  # type: (str) -> Optional[str]
        return sysconfig.get_path(path, vars=self._env_vars)

    def _symlink_relative(self, path):  # type: (Optional[str]) -> None
        if not path:  # pragma: no cover
            return

        prefix = sysconfig.get_config_var('prefix')
        if prefix and path and path.startswith(prefix):
            new_path = os.path.join(self.path, path[len(prefix + os.pathsep):])
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

    def __enter__(self):  # type: () -> IsolatedEnvironment
        self._path = tempfile.mkdtemp(prefix='build-env-')
        self._env_vars = {
            'base': self.path,
            'platbase': self.path,
        }

        sys_path = sys.path[1:]

        for path in self.MANIPULATE_PATHS:
            env_path = self._get_env_path(path)
            if env_path:
                sys_path.append(env_path)

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
        self._replace_env('PYTHONHOME', self.path)

        self._symlink_relative(sysconfig.get_path('include'))
        self._symlink_relative(sysconfig.get_path('platinclude'))
        self._symlink_relative(sysconfig.get_config_var('LIBPL'))

        return self

    def __exit__(self, typ, value, traceback):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[types.TracebackType]) -> None
        if self.path and os.path.isdir(self.path):
            shutil.rmtree(self.path)

        self._restore_env()

    def install(self, requirements):  # type: (Iterable[str]) -> None
        '''
        Installs the specified requirements on the environment
        '''
        if not requirements:
            return

        subprocess.check_call([sys.executable, '-m', 'ensurepip'], cwd=self.path)

        with tempfile.NamedTemporaryFile('w+', prefix='build-reqs-', suffix='.txt', delete=False) as req_file:
            req_file.write(os.linesep.join(requirements))
            req_file.close()
            cmd = [
                sys.executable, '-m', 'pip', 'install', '--prefix',
                self.path, '-r', os.path.abspath(req_file.name)
            ]
            subprocess.check_call(cmd)
            os.unlink(req_file.name)
