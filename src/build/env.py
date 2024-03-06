from __future__ import annotations

import abc
import functools
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import typing

from collections.abc import Collection, Mapping

from . import _ctx
from ._ctx import run_subprocess
from ._exceptions import FailedProcessError
from ._util import check_dependency


EnvImpl = typing.Literal['venv+uv']

ENV_IMPLS = typing.get_args(EnvImpl)


class IsolatedEnv(typing.Protocol):
    """Isolated build environment ABC."""

    @property
    @abc.abstractmethod
    def python_executable(self) -> str:
        """The Python executable of the isolated environment."""

    @abc.abstractmethod
    def make_extra_environ(self) -> Mapping[str, str] | None:
        """Generate additional env vars specific to the isolated environment."""


@functools.lru_cache(maxsize=None)
def _has_virtualenv() -> bool:
    from packaging.requirements import Requirement

    # virtualenv might be incompatible if it was installed separately
    # from build. This verifies that virtualenv and all of its
    # dependencies are installed as specified by build.
    return importlib.util.find_spec('virtualenv') is not None and not any(
        Requirement(d[1]).name == 'virtualenv' for d in check_dependency('build[virtualenv]') if len(d) > 1
    )


def _minimum_pip_version_str() -> str:
    if platform.system() == 'Darwin':
        release, _, machine = platform.mac_ver()
        if int(release[: release.find('.')]) >= 11:
            # macOS 11+ name scheme change requires 20.3. Intel macOS 11.0 can be
            # told to report 10.16 for backwards compatibility; but that also fixes
            # earlier versions of pip so this is only needed for 11+.
            is_apple_silicon_python = machine != 'x86_64'
            return '21.0.1' if is_apple_silicon_python else '20.3.0'

    # PEP-517 and manylinux1 was first implemented in 19.1
    return '19.1.0'


def _has_valid_pip(version_str: str | None = None, /, **distargs: object) -> bool:
    """
    Given a path, see if Pip is present and return True if the version is
    sufficient for build, False if it is not. ModuleNotFoundError is thrown if
    pip is not present.
    """

    from packaging.version import Version

    from ._compat import importlib

    name = 'pip'

    try:
        pip_distribution = next(iter(importlib.metadata.distributions(name=name, **distargs)))
    except StopIteration:
        raise ModuleNotFoundError(name) from None

    return Version(pip_distribution.version) >= Version(version_str or _minimum_pip_version_str())


class DefaultIsolatedEnv(IsolatedEnv):
    """
    Isolated environment which supports several different underlying implementations.
    """

    def __init__(
        self,
        env_impl: EnvImpl | None = None,
    ) -> None:
        self.env_impl = env_impl

    def __enter__(self) -> DefaultIsolatedEnv:
        try:
            path = tempfile.mkdtemp(prefix='build-env-')
            # Call ``realpath`` to prevent spurious warning from being emitted
            # that the venv location has changed on Windows for the venv impl.
            # The username is DOS-encoded in the output of tempfile - the location is the same
            # but the representation of it is different, which confuses venv.
            # Ref: https://bugs.python.org/issue46171
            path = os.path.realpath(path)
            self._path = path

            msg_tpl = 'Creating isolated environment: {}...'

            self._env_impl_backend: _EnvImplBackend

            # uv is opt-in only.
            if self.env_impl == 'venv+uv':
                _ctx.log(msg_tpl.format(self.env_impl))
                self._env_impl_backend = _UvImplBackend()

            # Use virtualenv when available (as seeding pip is faster than with venv).
            elif _has_virtualenv():
                _ctx.log(msg_tpl.format('virtualenv+pip'))
                self._env_impl_backend = _VirtualenvImplBackend()

            else:
                _ctx.log(msg_tpl.format('venv+pip'))
                self._env_impl_backend = _VenvImplBackend()

            self._env_impl_backend.create(self._path)

        except Exception:  # cleanup folder if creation fails
            self.__exit__(*sys.exc_info())
            raise

        return self

    def __exit__(self, *args: object) -> None:
        if os.path.exists(self._path):  # in case the user already deleted skip remove
            shutil.rmtree(self._path)

    @property
    def path(self) -> str:
        """The location of the isolated build environment."""
        return self._path

    @property
    def python_executable(self) -> str:
        """The python executable of the isolated build environment."""
        return self._env_impl_backend.python_executable

    def make_extra_environ(self) -> dict[str, str]:
        path = os.environ.get('PATH')
        return {
            'PATH': os.pathsep.join([self._env_impl_backend.scripts_dir, path])
            if path is not None
            else self._env_impl_backend.scripts_dir
        }

    def install(self, requirements: Collection[str]) -> None:
        """
        Install packages from PEP 508 requirements in the isolated build environment.

        :param requirements: PEP 508 requirement specification to install

        :note: Passing non-PEP 508 strings will result in undefined behavior, you *should not* rely on it. It is
               merely an implementation detail, it may change any time without warning.
        """
        if not requirements:
            return

        _ctx.log('Installing packages in isolated environment:\n' + '\n'.join(f'- {r}' for r in sorted(requirements)))
        self._env_impl_backend.install_requirements(requirements)


class _EnvImplBackend(typing.Protocol):  # pragma: no cover
    python_executable: str
    scripts_dir: str

    def create(self, path: str) -> None:
        ...

    def install_requirements(self, requirements: Collection[str]) -> None:
        ...


class _PipInstallBackendStub(_EnvImplBackend, typing.Protocol):
    @functools.cached_property
    def _has_valid_outer_pip(self) -> bool | None:
        """
        This checks for a valid global pip. Returns None if pip is missing, False
        if pip is too old, and True if it can be used.
        """
        try:
            # Version to have added the `--python` option.
            return _has_valid_pip('22.3')
        except ModuleNotFoundError:
            return None

    def install_requirements(self, requirements: Collection[str]) -> None:
        # pip does not honour environment markers in command line arguments
        # but it does from requirement files.
        with tempfile.NamedTemporaryFile('w', prefix='build-reqs-', suffix='.txt', delete=False, encoding='utf-8') as req_file:
            req_file.write(os.linesep.join(requirements))

        try:
            if self._has_valid_outer_pip:
                cmd = [sys.executable, '-m', 'pip', '--python', self.python_executable]
            else:
                cmd = [self.python_executable, '-Im', 'pip']

            if _ctx.verbosity > 1:
                cmd += [f'-{"v" * (_ctx.verbosity - 1)}']

            cmd += ['install', '--use-pep517', '--no-warn-script-location', '-r', os.path.abspath(req_file.name)]
            run_subprocess(cmd)

        finally:
            os.unlink(req_file.name)


class _VenvImplBackend(_PipInstallBackendStub):
    def create(self, path: str) -> None:
        import venv

        try:
            venv.EnvBuilder(symlinks=_fs_supports_symlink(), with_pip=not self._has_valid_outer_pip).create(path)
        except subprocess.CalledProcessError as exc:
            _ctx.log_subprocess_error(exc)
            raise FailedProcessError(exc, 'Failed to create venv. Maybe try installing virtualenv.') from None

        self.python_executable, self.scripts_dir, purelib = _find_executable_and_scripts(path)

        if not self._has_valid_outer_pip:
            # Get the version of pip in the environment
            if not _has_valid_pip(path=[purelib]):
                run_subprocess([self.python_executable, '-Im', 'pip', 'install', f'pip>={_minimum_pip_version_str()}'])
            run_subprocess([self.python_executable, '-Im', 'pip', 'uninstall', '-y', 'setuptools'])


class _VirtualenvImplBackend(_PipInstallBackendStub):
    def create(self, path: str) -> None:
        import virtualenv

        cmd = [path, '--activators', '']
        cmd += ['--no-seed'] if self._has_valid_outer_pip else ['--no-setuptools', '--no-wheel']

        result = virtualenv.cli_run(cmd, setup_logging=False)

        # The creator attributes are `pathlib.Path`s.
        self.python_executable = str(result.creator.exe)
        self.scripts_dir = str(result.creator.script_dir)


class _UvImplBackend(_EnvImplBackend):
    def create(self, path: str) -> None:
        import venv

        venv.EnvBuilder(symlinks=_fs_supports_symlink(), with_pip=False).create(path)

        self.python_executable, self.scripts_dir, _ = _find_executable_and_scripts(path)
        self._env_path = path

    def install_requirements(self, requirements: Collection[str]) -> None:
        import uv

        cmd = [uv.find_uv_bin(), 'pip']
        if _ctx.verbosity > 1:
            # uv doesn't support doubling up -v unlike pip.
            cmd += ['-v']
        run_subprocess([*cmd, 'install', *requirements], env={**os.environ, 'VIRTUAL_ENV': self._env_path})


@functools.lru_cache(maxsize=None)
def _fs_supports_symlink() -> bool:
    """Return True if symlinks are supported"""
    # Using definition used by venv.main()
    if os.name != 'nt':
        return True

    # Windows may support symlinks (setting in Windows 10)
    with tempfile.NamedTemporaryFile(prefix='build-symlink-') as tmp_file:
        dest = f'{tmp_file}-b'
        try:
            os.symlink(tmp_file.name, dest)
            os.unlink(dest)
        except (OSError, NotImplementedError, AttributeError):
            return False
        return True


def _find_executable_and_scripts(path: str) -> tuple[str, str, str]:
    """
    Detect the Python executable and script folder of a virtual environment.

    :param path: The location of the virtual environment
    :return: The Python executable, script folder, and purelib folder
    """
    config_vars = sysconfig.get_config_vars().copy()  # globally cached, copy before altering it
    config_vars['base'] = path
    scheme_names = sysconfig.get_scheme_names()
    if 'venv' in scheme_names:
        # Python distributors with custom default installation scheme can set a
        # scheme that can't be used to expand the paths in a venv.
        # This can happen if build itself is not installed in a venv.
        # The distributors are encouraged to set a "venv" scheme to be used for this.
        # See https://bugs.python.org/issue45413
        # and https://github.com/pypa/virtualenv/issues/2208
        paths = sysconfig.get_paths(scheme='venv', vars=config_vars)
    elif 'posix_local' in scheme_names:
        # The Python that ships on Debian/Ubuntu varies the default scheme to
        # install to /usr/local
        # But it does not (yet) set the "venv" scheme.
        # If we're the Debian "posix_local" scheme is available, but "venv"
        # is not, we use "posix_prefix" instead which is venv-compatible there.
        paths = sysconfig.get_paths(scheme='posix_prefix', vars=config_vars)
    elif 'osx_framework_library' in scheme_names:
        # The Python that ships with the macOS developer tools varies the
        # default scheme depending on whether the ``sys.prefix`` is part of a framework.
        # But it does not (yet) set the "venv" scheme.
        # If the Apple-custom "osx_framework_library" scheme is available but "venv"
        # is not, we use "posix_prefix" instead which is venv-compatible there.
        paths = sysconfig.get_paths(scheme='posix_prefix', vars=config_vars)
    else:
        paths = sysconfig.get_paths(vars=config_vars)

    executable = os.path.join(paths['scripts'], 'python.exe' if os.name == 'nt' else 'python')
    if not os.path.exists(executable):
        msg = f'Virtual environment creation failed, executable {executable} missing'
        raise RuntimeError(msg)

    return executable, paths['scripts'], paths['purelib']


__all__ = [
    'IsolatedEnv',
    'DefaultIsolatedEnv',
]
