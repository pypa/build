# SPDX-License-Identifier: MIT
from __future__ import annotations

import logging
import platform
import subprocess
import sys
import sysconfig

from pathlib import Path
from types import SimpleNamespace

import pytest
import pytest_mock

from packaging.version import Version

import build.env


IS_PYPY3 = platform.python_implementation() == 'PyPy'


@pytest.mark.isolated
@pytest.mark.parametrize('env_impl', build.env.ENV_IMPLS)
def test_isolation(
    env_impl: build.env.EnvImpl,
):
    subprocess.check_call([sys.executable, '-c', 'import build.env'])
    with build.env.DefaultIsolatedEnv(env_impl) as env:
        with pytest.raises(subprocess.CalledProcessError):
            debug = 'import sys; import os; print(os.linesep.join(sys.path));'
            subprocess.check_call([env.python_executable, '-c', f'{debug} import build.env'])


@pytest.mark.skipif(IS_PYPY3, reason='PyPy3 uses get path to create and provision venv')
@pytest.mark.skipif(sys.platform != 'darwin', reason='workaround for Apple Python')
def test_can_get_venv_paths_with_conflicting_default_scheme(
    mocker: pytest_mock.MockerFixture,
):
    get_scheme_names = mocker.patch('sysconfig.get_scheme_names', return_value=('osx_framework_library',))
    with build.env.DefaultIsolatedEnv():
        pass
    assert get_scheme_names.call_count == 1


@pytest.mark.skipif('posix_local' not in sysconfig.get_scheme_names(), reason='workaround for Debian/Ubuntu Python')
def test_can_get_venv_paths_with_posix_local_default_scheme(
    mocker: pytest_mock.MockerFixture,
):
    get_paths = mocker.spy(sysconfig, 'get_paths')
    # We should never call this, but we patch it to ensure failure if we do
    get_default_scheme = mocker.patch('sysconfig.get_default_scheme', return_value='posix_local')
    with build.env.DefaultIsolatedEnv():
        pass
    get_paths.assert_called_once_with(scheme='posix_prefix', vars=mocker.ANY)
    assert get_default_scheme.call_count == 0


def test_venv_impl_executable_missing_post_creation(
    mocker: pytest_mock.MockerFixture,
):
    venv_create = mocker.patch('venv.EnvBuilder.create')
    with pytest.raises(RuntimeError, match='Virtual environment creation failed, executable .* missing'):
        with build.env.DefaultIsolatedEnv():
            pass
    assert venv_create.call_count == 1


def test_isolated_env_abstract():
    with pytest.raises(TypeError):
        build.env.IsolatedEnv()

    class PartialEnv(build.env.IsolatedEnv):
        @property
        def executable(self):
            raise NotImplementedError

    with pytest.raises(TypeError):
        PartialEnv()

    class PartialEnv(build.env.IsolatedEnv):
        def make_extra_environ(self):
            return super().make_extra_environ()

    with pytest.raises(TypeError):
        PartialEnv()


@pytest.mark.pypy3323bug
def test_isolated_env_log(
    caplog: pytest.LogCaptureFixture,
    mocker: pytest_mock.MockerFixture,
):
    caplog.set_level(logging.DEBUG)
    mocker.patch('build.env.run_subprocess')

    with build.env.DefaultIsolatedEnv() as env:
        env.install(['something'])

    assert [(record.levelname, record.message) for record in caplog.records] == [
        ('INFO', 'Creating isolated environment: venv+pip...'),
        ('INFO', 'Installing packages in isolated environment:\n- something'),
    ]


@pytest.mark.isolated
@pytest.mark.usefixtures('local_pip')
def test_default_pip_is_never_too_old():
    with build.env.DefaultIsolatedEnv() as env:
        version = subprocess.check_output(
            [env.python_executable, '-c', 'import pip; print(pip.__version__, end="")'],
            encoding='utf-8',
        )
        assert Version(version) >= Version('19.1')


@pytest.mark.isolated
@pytest.mark.parametrize('pip_version', ['20.2.0', '20.3.0', '21.0.0', '21.0.1'])
@pytest.mark.parametrize('arch', ['x86_64', 'arm64'])
@pytest.mark.usefixtures('local_pip')
def test_pip_needs_upgrade_mac_os_11(
    mocker: pytest_mock.MockerFixture,
    pip_version: str,
    arch: str,
):
    run_subprocess = mocker.patch('build.env.run_subprocess')
    mocker.patch('platform.system', return_value='Darwin')
    mocker.patch('platform.mac_ver', return_value=('11.0', ('', '', ''), arch))
    mocker.patch('build._compat.importlib.metadata.distributions', return_value=(SimpleNamespace(version=pip_version),))

    min_version = Version('20.3' if arch == 'x86_64' else '21.0.1')
    with build.env.DefaultIsolatedEnv():
        if Version(pip_version) < min_version:
            upgrade_call, uninstall_call = run_subprocess.call_args_list
            answer = 'pip>=20.3.0' if arch == 'x86_64' else 'pip>=21.0.1'
            assert upgrade_call[0][0][1:] == ['-Im', 'pip', 'install', answer]
            assert uninstall_call[0][0][1:] == ['-Im', 'pip', 'uninstall', '-y', 'setuptools']
        else:
            (uninstall_call,) = run_subprocess.call_args_list
            assert uninstall_call[0][0][1:] == ['-Im', 'pip', 'uninstall', '-y', 'setuptools']


@pytest.mark.parametrize('has_symlink', [True, False] if sys.platform.startswith('win') else [True])
def test_venv_symlink(
    mocker: pytest_mock.MockerFixture,
    has_symlink: bool,
):
    if has_symlink:
        mocker.patch('os.symlink')
        mocker.patch('os.unlink')
    else:
        mocker.patch('os.symlink', side_effect=OSError())

    # Cache must be cleared to rerun
    build.env._fs_supports_symlink.cache_clear()
    supports_symlink = build.env._fs_supports_symlink()
    build.env._fs_supports_symlink.cache_clear()

    assert supports_symlink is has_symlink


@pytest.mark.parametrize('env_impl', build.env.ENV_IMPLS)
def test_install_short_circuits(
    mocker: pytest_mock.MockerFixture,
    env_impl: build.env.EnvImpl,
):
    with build.env.DefaultIsolatedEnv(env_impl) as env:
        install_requirements = mocker.patch.object(env._env_impl_backend, 'install_requirements')

        env.install([])
        install_requirements.assert_not_called()

        env.install(['foo'])
        install_requirements.assert_called_once()


@pytest.mark.usefixtures('local_pip')
@pytest.mark.parametrize('env_impl', ['virtualenv', 'venv'])
def test_venv_or_virtualenv_impl_install_cmd_well_formed(
    mocker: pytest_mock.MockerFixture,
    env_impl: build.env.EnvImpl,
):
    with build.env.DefaultIsolatedEnv(env_impl) as env:
        run_subprocess = mocker.patch('build.env.run_subprocess')

        env.install(['some', 'requirements'])

        run_subprocess.assert_called_once()
        call_args = run_subprocess.call_args[0][0][:-1]
        assert call_args == [
            env.python_executable,
            '-Im',
            'pip',
            'install',
            '--use-pep517',
            '--no-warn-script-location',
            '-r',
        ]


def test_uv_impl_install_cmd_well_formed(
    mocker: pytest_mock.MockerFixture,
):
    with build.env.DefaultIsolatedEnv('venv+uv') as env:
        run_subprocess = mocker.patch('build.env.run_subprocess')

        env.install(['foo'])

        (install_call,) = run_subprocess.call_args_list
        assert len(install_call.args) == 1
        assert install_call.args[0][1:] == ['pip', 'install', 'foo']
        assert len(install_call.kwargs) == 1
        assert install_call.kwargs['env']['VIRTUAL_ENV'] == env.path


@pytest.mark.parametrize(
    ('env_impl', 'backend_cls', 'has_virtualenv'),
    [
        (None, build.env._VenvImplBackend, False),
        (None, build.env._VirtualenvImplBackend, True),
        ('venv+uv', build.env._UvImplBackend, None),
    ],
    indirect=('has_virtualenv',),
)
def test_uv_venv_creation(
    env_impl: build.env.EnvImpl | None,
    backend_cls: build.env._EnvImplBackend,
):
    with build.env.DefaultIsolatedEnv(env_impl) as env:
        assert type(env._env_impl_backend) is backend_cls


@pytest.mark.network
@pytest.mark.usefixtures('local_pip')
@pytest.mark.parametrize('env_impl', build.env.ENV_IMPLS)
def test_requirement_installation(
    package_test_flit: str,
    env_impl: build.env.EnvImpl,
):
    with build.env.DefaultIsolatedEnv(env_impl) as env:
        env.install([f'test-flit @ {Path(package_test_flit).as_uri()}'])
