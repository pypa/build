# SPDX-License-Identifier: MIT
import collections
import logging
import platform
import subprocess
import sys
import sysconfig

import pytest

from packaging.version import Version

import build.env


IS_PYPY3 = platform.python_implementation() == 'PyPy'


@pytest.mark.isolated
def test_isolation():
    subprocess.check_call([sys.executable, '-c', 'import build.env'])
    with build.env.DefaultIsolatedEnv() as env:
        with pytest.raises(subprocess.CalledProcessError):
            debug = 'import sys; import os; print(os.linesep.join(sys.path));'
            subprocess.check_call([env.python_executable, '-c', f'{debug} import build.env'])


@pytest.mark.isolated
@pytest.mark.usefixtures('local_pip')
def test_isolated_environment_install(mocker):
    with build.env.DefaultIsolatedEnv() as env:
        mocker.patch('build.env._subprocess')

        env.install([])
        build.env._subprocess.assert_not_called()

        env.install(['some', 'requirements'])
        build.env._subprocess.assert_called()
        args = build.env._subprocess.call_args[0][0][:-1]
        assert args == [
            env.python_executable,
            '-Im',
            'pip',
            'install',
            '--use-pep517',
            '--no-warn-script-location',
            '-r',
        ]


@pytest.mark.skipif(IS_PYPY3, reason='PyPy3 uses get path to create and provision venv')
@pytest.mark.skipif(sys.platform != 'darwin', reason='workaround for Apple Python')
def test_can_get_venv_paths_with_conflicting_default_scheme(mocker):
    get_scheme_names = mocker.patch('sysconfig.get_scheme_names', return_value=('osx_framework_library',))
    with build.env.DefaultIsolatedEnv():
        pass
    assert get_scheme_names.call_count == 1


@pytest.mark.skipif('posix_local' not in sysconfig.get_scheme_names(), reason='workaround for Debian/Ubuntu Python')
def test_can_get_venv_paths_with_posix_local_default_scheme(mocker):
    get_paths = mocker.spy(sysconfig, 'get_paths')
    # We should never call this, but we patch it to ensure failure if we do
    get_default_scheme = mocker.patch('sysconfig.get_default_scheme', return_value='posix_local')
    with build.env.DefaultIsolatedEnv():
        pass
    get_paths.assert_called_once_with(scheme='posix_prefix', vars=mocker.ANY)
    assert get_default_scheme.call_count == 0


def test_executable_missing_post_creation(mocker):
    venv_create = mocker.patch('venv.EnvBuilder.create')
    with pytest.raises(RuntimeError, match='Virtual environment creation failed, executable .* missing'):
        with build.env.DefaultIsolatedEnv():
            pass
    assert venv_create.call_count == 1


def test_isolated_env_abstract():
    with pytest.raises(TypeError):
        build.env.IsolatedEnv()


def test_isolated_env_has_executable_still_abstract():
    class Env(build.env.IsolatedEnv):
        @property
        def executable(self):
            raise NotImplementedError

    with pytest.raises(TypeError):
        Env()


def test_isolated_env_has_install_still_abstract():
    class Env(build.env.IsolatedEnv):
        def install(self, requirements):
            raise NotImplementedError

    with pytest.raises(TypeError):
        Env()


@pytest.mark.pypy3323bug
def test_isolated_env_log(mocker, caplog, package_test_flit):
    mocker.patch('build.env._subprocess')
    caplog.set_level(logging.DEBUG)

    builder = build.env.DefaultIsolatedEnv()
    builder.log('something')  # line number 106
    with builder as env:
        env.install(['something'])

    assert [(record.levelname, record.message) for record in caplog.records] == [
        ('INFO', 'something'),
        ('INFO', 'Creating venv isolated environment...'),
        ('INFO', 'Installing packages in isolated environment... (something)'),
    ]


@pytest.mark.isolated
@pytest.mark.usefixtures('local_pip')
def test_default_pip_is_never_too_old():
    with build.env.DefaultIsolatedEnv() as env:
        version = subprocess.check_output(
            [env.python_executable, '-c', 'import pip; print(pip.__version__)'],
            text=True,
            encoding='utf-8',
        ).strip()
        assert Version(version) >= Version('19.1')


@pytest.mark.isolated
@pytest.mark.parametrize('pip_version', ['20.2.0', '20.3.0', '21.0.0', '21.0.1'])
@pytest.mark.parametrize('arch', ['x86_64', 'arm64'])
@pytest.mark.usefixtures('local_pip')
def test_pip_needs_upgrade_mac_os_11(mocker, pip_version, arch):
    SimpleNamespace = collections.namedtuple('SimpleNamespace', 'version')

    _subprocess = mocker.patch('build.env._subprocess')
    mocker.patch('platform.system', return_value='Darwin')
    mocker.patch('platform.machine', return_value=arch)
    mocker.patch('platform.mac_ver', return_value=('11.0', ('', '', ''), ''))
    mocker.patch('build._compat.importlib.metadata.distributions', return_value=(SimpleNamespace(version=pip_version),))

    min_version = Version('20.3' if arch == 'x86_64' else '21.0.1')
    with build.env.DefaultIsolatedEnv():
        if Version(pip_version) < min_version:
            print(_subprocess.call_args_list)
            upgrade_call, uninstall_call = _subprocess.call_args_list
            answer = 'pip>=20.3.0' if arch == 'x86_64' else 'pip>=21.0.1'
            assert upgrade_call[0][0][1:] == ['-m', 'pip', 'install', answer]
            assert uninstall_call[0][0][1:] == ['-m', 'pip', 'uninstall', 'setuptools', '-y']
        else:
            (uninstall_call,) = _subprocess.call_args_list
            assert uninstall_call[0][0][1:] == ['-m', 'pip', 'uninstall', 'setuptools', '-y']


@pytest.mark.isolated
@pytest.mark.skipif(IS_PYPY3 and sys.platform.startswith('win'), reason='Isolated tests not supported on PyPy3 + Windows')
@pytest.mark.parametrize('has_symlink', [True, False] if sys.platform.startswith('win') else [True])
def test_venv_symlink(mocker, has_symlink):
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
