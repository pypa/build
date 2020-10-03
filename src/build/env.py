import collections
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import types

from typing import Dict, Iterable, Optional, Sequence, Type


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
        '''
        :param remove_paths: Import paths that should be removed from the environment
        '''
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
        '''
        Creates an isolated environment for the current interpreter
        '''
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
        '''
        Replaces an environment variable
        '''
        if not new:  # pragma: no cover
            return

        self._env[key] = os.environ.get(key, None)
        os.environ[key] = new

    def _pop_env(self, key):  # type: (str) -> None
        '''
        Removes an environment variable
        '''
        self._env[key] = os.environ.pop(key, None)

    def _restore_env(self):  # type: () -> None
        '''
        Restores the initial environment variables
        '''
        for key, val in self._env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def _get_env_path(self, path):  # type: (str) -> Optional[str]
        '''
        Returns sysconfig path from our environment
        '''
        return sysconfig.get_path(path, vars=self._env_vars)

    def _symlink_or_copy_file(self, path, new_subpath):  # type: (str, str) -> None
        '''
        Places a file into our environment

        :param path: File to be symlinked
        :param new_subpath: Subpath of target destination
        '''
        new_path = os.path.join(self.path, new_subpath)
        dir_path = os.path.dirname(new_path)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        if fs_supports_symlink():
            os.symlink(path, new_path)
        else:
            shutil.copyfile(path, new_path)

    def _symlink_or_copy_path_relative(self, path):  # type: (Optional[str]) -> None
        '''
        Places a path into our environment

        The original prefix will be removed and replaced with our environmenmt's

        If the path is not valid, nothing will happen
        '''
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
                    shutil.copytree(path, new_path)

    def __enter__(self):  # type: () -> IsolatedEnvironment
        '''
        Set up the environment

        The environment path should be empty
        '''
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

        '''
        Place include, platinclude and LIBPL into our environment. They should
        be present and may be used to compile native packages or similar.
        '''
        self._symlink_or_copy_path_relative(sysconfig.get_path('include'))
        self._symlink_or_copy_path_relative(sysconfig.get_path('platinclude'))
        self._symlink_or_copy_path_relative(sysconfig.get_config_var('LIBPL'))

        '''
        We use PYTHONHOME to relocate the Python installation to our environment,
        but turns out this can't be blindely relied upon, *sigh*. If a pyvenv.cfg
        file is present on the same directory than the binary or one level above,
        data, platlib, platstdlib, purelib and scripts will be overritten. So we
        need to make sure that doesn't happen, hence we symlink the Python
        executable onto a path we control and use that binary for the enrionment.

        Unfortunately, this forces us to override sys.executable. There is no
        other way of doing it.
        '''
        executable_dir = 'executable'
        executable_path = os.path.join(self.path, executable_dir)
        self._symlink_or_copy_file(sys.executable, os.path.join(executable_dir, 'python'))
        exe_path.insert(0, executable_path)

        self._executable = sys.executable
        sys.executable = os.path.join(executable_path, 'python')

        # Replace PATH with our value for the environment
        self._replace_env('PATH', os.pathsep.join(
            list(collections.OrderedDict.fromkeys(exe_path))  # remove duplicates, need OrderedDict on Python <3.7
        ))

        # Inject the missing import paths via PYTHONPATH
        self._replace_env('PYTHONPATH', os.pathsep.join(sys_path))

        # Point the Python interpreter to our environment
        self._replace_env('PYTHONHOME', self.path)

        # Remove environment variables that intrefer with our use of pip
        self._pop_env('PIP_REQUIRE_VIRTUALENV')

        return self

    def __exit__(self, typ, value, traceback):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[types.TracebackType]) -> None
        '''
        Restores the everything to the original state
        '''
        if self.path and os.path.isdir(self.path):
            shutil.rmtree(self.path)

        self._restore_env()
        sys.executable = self._executable

    def install(self, requirements):  # type: (Iterable[str]) -> None
        '''
        Installs the specified PEP 508 requirements on the environment

        Passing non PEP 508 strings will result in undefined behavior, you
        *should not* rely on it. It is merely an implementation detail, it may
        change any time without warning.
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
