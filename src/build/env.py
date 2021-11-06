"""
Creates and manages isolated build environments.
"""

import abc
import logging
import os
import platform
import shutil
import sys
import sysconfig
import tempfile

from typing import Dict, Iterable, Optional, Sequence, Tuple

from ._helpers import cache, check_dependency, default_runner


_logger = logging.getLogger(__name__)


class IsolatedEnv(metaclass=abc.ABCMeta):
    """ABC for isolated build environments."""

    @abc.abstractmethod
    def create(self, path: str) -> None:
        """
        Create the isolated environment.

        This method should be idempotent.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def prepare_environ(self) -> Optional[Dict[str, str]]:
        """
        Modify environment variables.
        """
        raise NotImplementedError

    @abc.abstractproperty
    def python_executable(self) -> str:
        """The isolated environment's Python executable."""
        raise NotImplementedError


@cache
def _fs_supports_symlinks() -> bool:
    """Check if symlinks are supported."""
    # Using definition used by venv.main()
    if os.name != 'nt':
        return True

    # Windows may support symlinks (setting in Windows 10)
    with tempfile.TemporaryDirectory(prefix='build-try-symlink-') as temp_dir:
        try:
            os.symlink(
                os.path.join(temp_dir, 'foo'),
                os.path.join(temp_dir, 'bar'),
            )
            return True
        except (OSError, NotImplementedError, AttributeError):
            return False


def _get_isolated_env_executable_and_paths(path: str) -> Tuple[str, Dict[str, str]]:
    """
    :param path: venv path on disk
    :returns: The Python executable and scripts folder
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
        raise RuntimeError(f'Virtual environment creation failed, executable {executable} missing')
    return executable, paths


def _create_isolated_env_venv(path: str) -> Tuple[str, Dict[str, str]]:
    """
    :param path: venv path on disk
    :returns: The Python executable and scripts folder
    """
    import venv

    venv.EnvBuilder(symlinks=_fs_supports_symlinks(), with_pip=True).create(path)
    return _get_isolated_env_executable_and_paths(path)


def _create_isolated_env_virtualenv(path: str) -> Tuple[str, str]:
    """
    :param path: virtualenv path on disk
    :returns: The Python executable and scripts folder
    """
    import virtualenv

    cmd = [str(path), '--no-setuptools', '--no-wheel', '--activators', '']
    result = virtualenv.cli_run(cmd, setup_logging=False)
    executable = str(result.creator.exe)
    script_dir = str(result.creator.script_dir)
    return executable, script_dir


@cache
def _should_use_virtualenv() -> bool:
    import packaging.requirements

    # virtualenv might be incompatible if it was installed separately
    # from build. This verifies that virtualenv and all of its
    # dependencies are installed as specified by build.
    return not any(
        packaging.requirements.Requirement(u).name == 'virtualenv' for d in check_dependency('build[virtualenv]') for u in d
    )


@cache
def _get_min_pip_version() -> str:
    if platform.system() == 'Darwin':
        release, _, machine = platform.mac_ver()

        # Apple Silicon support for wheels shipped with packaging 20.9,
        # vendored in pip 21.0.1.
        if machine == 'arm64':
            return '21.0.1'

        # macOS 11+ name scheme change requires 20.3. Intel macOS 11.0 can
        # be told to report 10.16 for backwards compatibility;
        # but that also fixes earlier versions of pip so this is only needed for 11+.
        major_version = int(release[: release.find('.')])
        if major_version >= 11:
            return '20.3'

    # PEP 517 and manylinux1 were first implemented in 19.1
    return '19.1'


class _DefaultIsolatedEnv(IsolatedEnv):
    """An isolated environment which combines venv or virtualenv with pip."""

    def __init__(self, isolated_env_manager: 'IsolatedEnvManager') -> None:
        self._log = isolated_env_manager.log
        self._env_created = False

    def _run(self, cmd: Sequence[str]) -> None:
        return default_runner(cmd, env=self.prepare_environ())

    def create(self, path: str) -> None:
        if self._env_created:
            return

        if _should_use_virtualenv():
            self._log('Creating isolated environment (virtualenv)...')
            self._python_executable, self._scripts_dir = _create_isolated_env_virtualenv(path)
        else:
            self._log('Creating isolated environment (venv)...')
            # Call ``realpath`` to prevent spurious warning from being emitted
            # that the venv location has changed on Windows. The username is
            # DOS-encoded in the output of tempfile - the location is the same
            # but the representation of it is different, which confuses venv.
            # Ref: https://bugs.python.org/issue46171
            path = os.path.realpath(tempfile.mkdtemp(prefix='build-env-'))
            self._python_executable, paths = _create_isolated_env_venv(path)
            self._scripts_dir = paths['scripts']
            self._patch_up_venv(paths['purelib'])

        self._env_created = True

    def _patch_up_venv(self, venv_purelib: str) -> None:
        import packaging.version

        if sys.version_info >= (3, 8):
            from importlib.metadata import distributions
        else:
            from importlib_metadata import distributions

        cur_pip_version = next(
            d.version for d in distributions(name='pip', path=[venv_purelib])  # type: ignore[no-untyped-call]
        )
        min_pip_version = _get_min_pip_version()
        if packaging.version.Version(cur_pip_version) < packaging.version.Version(min_pip_version):
            self._run([self.python_executable, '-m', 'pip', 'install', f'pip>={min_pip_version}'])

        self._run([self.python_executable, '-m', 'pip', 'uninstall', '-y', 'setuptools'])

    def install_packages(self, requirements: Iterable[str]) -> None:
        """
        Install packages in the isolated environment.

        :param requirements: PEP 508-style requirements
        """
        req_list = sorted(requirements)
        if not req_list:
            return

        # pip does not honour environment markers in command line arguments;
        # it does for requirements from a file.
        with tempfile.NamedTemporaryFile(
            'w',
            prefix='build-reqs-',
            suffix='.txt',
            # On Windows the temp file can't be opened by pip while it is kept open by build
            # so we defer deleting it.
            delete=False,
        ) as req_file:
            req_file.write(os.linesep.join(req_list))

        try:
            self._log(f'Installing build dependencies... ({", ".join(req_list)})')
            self._run(
                [
                    self.python_executable,
                    '-m',
                    'pip',
                    'install',
                    # Enforce PEP 517 because "legacy" builds won't work for build dependencies
                    # of a project which does not use setuptools.
                    '--use-pep517',
                    '-r',
                    req_file.name,
                ]
            )
        finally:
            os.unlink(req_file.name)

    def prepare_environ(self) -> Dict[str, str]:
        environ = os.environ.copy()

        # Make the virtual environment's scripts available to the project's build dependecies.
        path = environ.get('PATH')
        environ['PATH'] = os.pathsep.join([self._scripts_dir, path]) if path is not None else self._scripts_dir

        return environ

    @property
    def python_executable(self) -> str:
        return self._python_executable


class IsolatedEnvManager:
    """Create and dispose of isolated build environments."""

    def __enter__(self) -> _DefaultIsolatedEnv:
        """
        Create an isolated build environment.

        :returns: The isolated environment
        """
        self._path = tempfile.mkdtemp(prefix='build-env-')
        try:
            isolated_env = _DefaultIsolatedEnv(self)
            isolated_env.create(self._path)
            return isolated_env
        except Exception:  # Delete folder if creation fails
            self.__exit__(*sys.exc_info())
            raise

    def __exit__(self, *exc_info: object) -> None:
        if os.path.exists(self._path):
            shutil.rmtree(self._path)

    @staticmethod
    def log(message: str) -> None:
        """
        Log a message.

        The default implementation uses the logging module but this function can be
        overridden by users to have a different implementation.

        :param message: Message to log
        """
        if sys.version_info >= (3, 8):
            _logger.log(logging.INFO, message, stacklevel=2)
        else:
            _logger.log(logging.INFO, message)


__all__ = [
    'IsolatedEnvManager',
    'IsolatedEnv',
]
