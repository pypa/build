import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import types


if False:  # TYPE_CHECKING  # pragma: no cover
    from typing import Dict, Optional, Iterable, Type


class IsolatedEnvironment(object):
    '''
    Isolated build environment context manager

    Non-standard paths injected directly to sys.path still be passed to the environment.
    '''

    def __init__(self):  # type: () -> None
        self._env = {}  # type: Dict[str, Optional[str]]

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

    def __enter__(self):  # type: () -> IsolatedEnvironment
        self._path = tempfile.mkdtemp(prefix='build-env-')
        self._env_vars = {
            'base': self._path,
            'platbase': self._path,
        }

        sys_path = sys.path[1:]

        remove_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)

        for path in ('purelib', 'platlib'):
            our_path = sysconfig.get_path(path)
            if our_path:
                remove_paths.append(our_path)

            for scheme in sysconfig.get_scheme_names():
                our_path = sysconfig.get_path(path, scheme)
                if our_path:
                    remove_paths.append(our_path)

            env_path = self._get_env_path(path)
            if env_path:
                sys_path.append(env_path)

        for path in remove_paths:
            if path in sys_path:
                sys_path.remove(path)

        self._replace_env('PATH', self._get_env_path('scripts'))
        self._replace_env('PYTHONPATH', os.pathsep.join(sys_path))
        self._replace_env('PYTHONHOME', self._path)

        return self

    def __exit__(self, typ, value, traceback):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[types.TracebackType]) -> None
        if self._path and os.path.isdir(self._path):
            shutil.rmtree(self._path)

        self._restore_env()

    def install(self, requirements):  # type: (Iterable[str]) -> None
        '''
        Installs the specified requirements on the environment
        '''
        if not requirements:
            return

        subprocess.check_call([sys.executable, '-m', 'ensurepip'], cwd=self._path)

        cmd = [sys.executable, '-m', 'pip', 'install', '--ignore-installed', '--prefix', self._path] + list(requirements)
        subprocess.check_call(cmd)
