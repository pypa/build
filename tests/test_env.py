# SPDX-License-Identifier: MIT
import json
import os
import platform
import shutil
import subprocess
import sys
import sysconfig

import pytest

import build.env


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
            env._pip_executable,
            '-{}m'.format('E' if env._pip_executable == env._python_executable and sys.version_info[0] == 2 else ''),
            'pip',
            'install',
            '--prefix',
            env.path,
            '--ignore-installed',
            '--no-warn-script-location',
            '-r',
        ]


@pytest.mark.isolated
def test_create_isolated_build_host_with_no_pip(tmp_path, capfd, mocker):
    mocker.patch.object(build.env, 'pip', None)
    expected = {'pip', 'greenlet', 'readline', 'cffi'} if platform.python_implementation() == 'PyPy' else {'pip'}

    with build.env.IsolatedEnvBuilder() as isolated_env:
        cmd = [isolated_env.executable, '-m', 'pip', 'list', '--format', 'json']
        packages = {p['name'] for p in json.loads(subprocess.check_output(cmd, universal_newlines=True))}
        assert packages == expected
    assert isolated_env._pip_executable == isolated_env.executable
    out, err = capfd.readouterr()
    if sys.version_info[0] == 3:
        assert out  # ensurepip prints onto the stdout
    else:
        assert not out
    assert not err


@pytest.mark.isolated
def test_create_isolated_build_has_with_pip(tmp_path, capfd, mocker):
    with build.env.IsolatedEnvBuilder() as isolated_env:
        pass
    assert isolated_env._pip_executable == sys.executable
    out, err = capfd.readouterr()
    assert not out
    assert not err


@pytest.mark.skipif(sys.version_info[0] == 2, reason='venv module used on Python 3 only')
def test_fail_to_get_script_path(mocker):
    get_path = mocker.patch('sysconfig.get_path', return_value=None)
    with pytest.raises(RuntimeError, match="Couldn't get environment scripts path"):
        env = build.env.IsolatedEnvBuilder()
        with env:
            pass
    assert not os.path.exists(env._path)
    assert get_path.call_count == 1


@pytest.mark.skipif(sys.version_info[0] == 2, reason='venv module used on Python 3 only')
def test_executable_missing_post_creation(mocker):
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
