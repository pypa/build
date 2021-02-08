# SPDX-License-Identifier: MIT
import os
import platform
import shutil
import subprocess
import sys
import sysconfig

import pytest

import build.env


IS_PYPY3 = sys.version_info[0] == 3 and platform.python_implementation() == 'PyPy'


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
        if sys.version_info[:2] != (3, 5):
            subprocess.check_call.assert_called()
        args = subprocess.check_call.call_args[0][0][:-1]
        assert args == [
            env.executable,
            '-{}m'.format('E' if sys.version_info[0] == 2 else 'I'),
            'pip',
            'install',
            '--no-warn-script-location',
            '-r',
        ]


@pytest.mark.skipif(sys.version_info[0] == 2, reason='venv module used on Python 3 only')
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


@pytest.mark.skipif(sys.version_info[0] == 2, reason='venv module used on Python 3 only')
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
@pytest.mark.skipif(sys.version_info > (3, 6, 5), reason='inapplicable')
def test_default_pip_is_upgraded_on_python_3_6_5_and_below():
    with build.env.IsolatedEnvBuilder() as env:
        assert not subprocess.check_output([env.executable, '-m', 'pip', '-V']).startswith(b'pip 9.0')
