# SPDX-License-Identifier: MIT
import collections
import os
import platform
import shutil
import subprocess
import sys
import sysconfig

import pytest

from packaging.version import Version

import build.env


IS_PYPY3 = sys.version_info[0] == 3 and platform.python_implementation() == 'PyPy'
IS_PY35 = sys.version_info[:2] == (3, 5)
IS_PY2 = sys.version_info[0] == 2


@pytest.mark.isolated
def test_isolation():
    subprocess.check_call([sys.executable, '-c', 'import build.env'])
    with build.env.IsolatedEnvBuilder() as env:
        with pytest.raises(subprocess.CalledProcessError):
            debug = 'import sys; import os; print(os.linesep.join(sys.path));'
            subprocess.check_call([env.executable, '-c', '{} import build.env'.format(debug)])


@pytest.mark.isolated
def test_isolated_environment_install(mocker):
    with build.env.IsolatedEnvBuilder() as env:
        mocker.patch('subprocess.check_call')

        env.install([])
        subprocess.check_call.assert_not_called()

        env.install(['some', 'requirements'])
        if not IS_PY35:
            subprocess.check_call.assert_called()
        args = subprocess.check_call.call_args[0][0][:-1]
        assert args == [
            env.executable,
            '-{}m'.format('E' if IS_PY2 else 'I'),
            'pip',
            'install',
            '--use-pep517',
            '--no-warn-script-location',
            '-r',
        ]


@pytest.mark.skipif(IS_PY2, reason='venv module used on Python 3 only')
@pytest.mark.skipif(IS_PYPY3, reason='PyPy3 uses get path to create and provision venv')
def test_fail_to_get_script_path(mocker):
    mocker.patch.object(build.env, 'virtualenv', None)
    get_path = mocker.patch('sysconfig.get_path', return_value=None)
    with pytest.raises(RuntimeError, match="Couldn't get environment scripts path"):
        env = build.env.IsolatedEnvBuilder()
        with env:
            pass
    assert not os.path.exists(env._path)
    assert get_path.call_count == 1


@pytest.mark.skipif(IS_PY2, reason='venv module used on Python 3 only')
@pytest.mark.skipif(IS_PYPY3, reason='PyPy3 uses get path to create and provision venv')
def test_fail_to_get_purepath(mocker):
    mocker.patch.object(build.env, 'virtualenv', None)
    sysconfig_get_path = sysconfig.get_path
    mocker.patch(
        'sysconfig.get_path',
        side_effect=lambda path, *args, **kwargs: '' if path == 'purelib' else sysconfig_get_path(path, *args, **kwargs),
    )

    with pytest.raises(RuntimeError, match="Couldn't get environment purelib folder"):
        with build.env.IsolatedEnvBuilder():
            pass


@pytest.mark.skipif(IS_PY2, reason='venv module used on Python 3 only')
@pytest.mark.skipif(IS_PYPY3, reason='PyPy3 uses get path to create and provision venv')
def test_executable_missing_post_creation(mocker):
    mocker.patch.object(build.env, 'virtualenv', None)
    original_get_path = sysconfig.get_path

    def _get_path(name, vars):  # noqa
        shutil.rmtree(vars['base'])
        return original_get_path(name, vars=vars)

    get_path = mocker.patch('sysconfig.get_path', side_effect=_get_path)
    with pytest.raises(RuntimeError, match='Virtual environment creation failed, executable .* missing'):
        with build.env.IsolatedEnvBuilder():
            pass
    assert get_path.call_count == 1


def test_isolated_env_abstract():
    with pytest.raises(TypeError):
        build.env.IsolatedEnv()


def test_isolated_env_has_executable_still_abstract():
    class Env(build.env.IsolatedEnv):  # noqa
        @property
        def executable(self):
            raise NotImplementedError

    with pytest.raises(TypeError):
        Env()


def test_isolated_env_has_install_still_abstract():
    class Env(build.env.IsolatedEnv):  # noqa
        def install(self, requirements):
            raise NotImplementedError

    with pytest.raises(TypeError):
        Env()


@pytest.mark.isolated
def test_default_pip_is_never_too_old():
    with build.env.IsolatedEnvBuilder() as env:
        version = subprocess.check_output(
            [env.executable, '-c', 'import pip; print(pip.__version__)'], universal_newlines=True
        ).strip()
        assert Version(version) >= Version('19.1')


@pytest.mark.isolated
@pytest.mark.parametrize('pip_version', ['20.2.0', '20.3.0', '21.0.0', '21.0.1'])
@pytest.mark.parametrize('arch', ['x86_64', 'arm64'])
@pytest.mark.skipif(IS_PY35, reason="Python 3.5 does not run on macOS 11, and pip can't upgrade to 21 there")
@pytest.mark.skipif(IS_PY2, reason='venv module used on Python 3 only')
def test_pip_needs_upgrade_mac_os_11(mocker, pip_version, arch):
    SimpleNamespace = collections.namedtuple('SimpleNamespace', 'version')

    check_call = mocker.patch('subprocess.check_call')
    mocker.patch('platform.system', return_value='Darwin')
    mocker.patch('platform.machine', return_value=arch)
    mocker.patch('platform.mac_ver', return_value=('11.0', ('', '', ''), ''))
    mocker.patch('build.env.metadata.distributions', return_value=(SimpleNamespace(version=pip_version),))
    mocker.patch.object(build.env, 'virtualenv', None)  # hide virtualenv

    min_version = Version('20.3' if arch == 'x86_64' else '21.0.1')
    with build.env.IsolatedEnvBuilder():
        if Version(pip_version) < min_version:
            upgrade_call, uninstall_call = check_call.call_args_list
            assert upgrade_call[0][0][1:] == ['-m', 'pip', 'install', '-U', 'pip']
            assert uninstall_call[0][0][1:] == ['-m', 'pip', 'uninstall', 'setuptools', '-y']
        else:
            (uninstall_call,) = check_call.call_args_list
            assert uninstall_call[0][0][1:] == ['-m', 'pip', 'uninstall', 'setuptools', '-y']
