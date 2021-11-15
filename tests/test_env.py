# SPDX-License-Identifier: MIT
import logging
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import types

import pytest

from packaging.version import Version

import build.env


IS_PYPY3 = platform.python_implementation() == 'PyPy'


@pytest.mark.isolated
def test_isolation():
    subprocess.check_call([sys.executable, '-c', 'import build.env'])
    with build.env.IsolatedEnvManager() as env:
        with pytest.raises(subprocess.CalledProcessError):
            debug = 'import sys; import os; print(os.linesep.join(sys.path));'
            subprocess.check_call([env.python_executable, '-c', f'{debug} import build.env'])


@pytest.mark.isolated
def test_isolated_environment_install(mocker):
    with build.env.IsolatedEnvManager() as env:
        mocker.patch('build.env._DefaultIsolatedEnv._run')

        env.install_packages([])
        build.env._DefaultIsolatedEnv._run.assert_not_called()

        env.install_packages(['some', 'requirements'])
        build.env._DefaultIsolatedEnv._run.assert_called()
        args = build.env._DefaultIsolatedEnv._run.call_args[0][0][:-1]
        assert args == [
            env.python_executable,
            '-m',
            'pip',
            'install',
            '--use-pep517',
            '-r',
        ]


@pytest.mark.skipif(IS_PYPY3, reason='PyPy3 uses get path to create and provision venv')
@pytest.mark.skipif(sys.platform != 'darwin', reason='workaround for Apple Python')
def test_can_get_venv_paths_with_conflicting_default_scheme(mocker):
    get_scheme_names = mocker.patch('sysconfig.get_scheme_names', return_value=('osx_framework_library',))
    with build.env.IsolatedEnvManager():
        pass
    assert get_scheme_names.call_count == 1


@pytest.mark.skipif(IS_PYPY3, reason='PyPy3 uses get path to create and provision venv')
def test_executable_missing_post_creation(mocker):
    original_get_paths = sysconfig.get_paths

    def _get_paths(vars):  # noqa
        shutil.rmtree(vars['base'])
        return original_get_paths(vars=vars)

    get_paths = mocker.patch('sysconfig.get_paths', side_effect=_get_paths)
    with pytest.raises(RuntimeError, match='Virtual environment creation failed, executable .* missing'):
        with build.env.IsolatedEnvManager():
            pass
    assert get_paths.call_count == 1


def test_isolated_env_abstract():
    with pytest.raises(TypeError):
        build.env.IsolatedEnv()


def test_isolated_env_log(mocker, caplog, package_test_flit):
    mocker.patch('build.env._DefaultIsolatedEnv._run')
    caplog.set_level(logging.DEBUG)

    builder = build.env.IsolatedEnvManager()
    with builder as env:
        env.log('something')
        env.install_packages(['something'])

    assert [(record.levelname, record.message) for record in caplog.records] == [
        ('INFO', 'Creating isolated environment (venv)...'),
        ('INFO', 'something'),
        ('INFO', 'Installing build dependencies... (something)'),
    ]
    if sys.version_info >= (3, 8):  # stacklevel
        assert [record.lineno for record in caplog.records] == [
            build.env._DefaultIsolatedEnv.create.__code__.co_firstlineno + 8,
            test_isolated_env_log.__code__.co_firstlineno + 6,
            build.env._DefaultIsolatedEnv.install_packages.__code__.co_firstlineno + 23,
        ]


@pytest.mark.isolated
def test_default_pip_is_never_too_old():
    with build.env.IsolatedEnvManager() as env:
        version = subprocess.check_output(
            [env.python_executable, '-c', 'import pip; print(pip.__version__)'], universal_newlines=True
        ).strip()
        assert Version(version) >= Version('19.1')


@pytest.mark.isolated
@pytest.mark.parametrize('arch', ['x86_64', 'arm64'])
@pytest.mark.parametrize('pip_version', ['20.2.0', '20.3.0', '21.0.0', '21.0.1'])
@pytest.mark.skipif(sys.platform != 'darwin', reason='mac only')
def test_pip_needs_upgrade_mac_os_11(mocker, arch, pip_version):
    _subprocess = mocker.patch('build.env._DefaultIsolatedEnv._run')
    mocker.patch('platform.system', return_value='Darwin')
    mocker.patch('platform.mac_ver', return_value=('11.0', ('', '', ''), arch))

    mocker.patch(
        'build._compat.importlib_metadata.distributions',
        return_value=iter([types.SimpleNamespace(version=pip_version)]),
    )

    # Cache must be cleared to rerun
    build.env._get_min_pip_version.cache_clear()
    min_version = build.env._get_min_pip_version()

    with build.env.IsolatedEnvManager():
        if Version(pip_version) < Version(min_version):
            print(_subprocess.call_args_list)
            upgrade_call, uninstall_call = _subprocess.call_args_list
            answer = 'pip>=20.3' if arch == 'x86_64' else 'pip>=21.0.1'
            assert upgrade_call[0][0][1:] == ['-m', 'pip', 'install', answer]
            assert uninstall_call[0][0][1:] == ['-m', 'pip', 'uninstall', '-y', 'setuptools']
        else:
            (uninstall_call,) = _subprocess.call_args_list
            assert uninstall_call[0][0][1:] == ['-m', 'pip', 'uninstall', '-y', 'setuptools']


@pytest.mark.isolated
@pytest.mark.skipif(IS_PYPY3 and os.name == 'nt', reason='Isolated tests not supported on PyPy3 + Windows')
@pytest.mark.parametrize('has_symlink', [True, False] if os.name == 'nt' else [True])
def test_venv_symlink(mocker, has_symlink):
    if has_symlink:
        mocker.patch('os.symlink')
        mocker.patch('os.unlink')
    else:
        mocker.patch('os.symlink', side_effect=OSError())

    # Cache must be cleared to rerun
    build.env._fs_supports_symlinks.cache_clear()
    supports_symlinks = build.env._fs_supports_symlinks()
    build.env._fs_supports_symlinks.cache_clear()

    assert supports_symlinks is has_symlink
