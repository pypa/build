# SPDX-License-Identifier: MIT
import json
import os
import os.path
import platform
import subprocess
import sys
import sysconfig

import pytest

import build.env


@pytest.mark.skipif(sys.version_info[0] != 2, reason='Custom isolated environment only available on Python 2')
def test_isolated_environment_setup():
    old_path = os.environ['PATH']
    with build.env.IsolatedEnvironment.for_current() as env:
        if os.name != 'nt':
            assert os.environ['PATH'] == os.pathsep.join([os.path.join(env.path, 'bin'), old_path])
        assert os.environ['PYTHONHOME'] == env.path

        python_path = map(os.path.normpath, os.environ['PYTHONPATH'].split(os.pathsep))
        for path in ('purelib', 'platlib'):
            sys_vars = {
                'base': env.path,
                'platbase': env.path,
            }
            assert os.path.normcase(sysconfig.get_path(path)) not in python_path
            assert os.path.normcase(sysconfig.get_path(path, vars=sys_vars)) in python_path

        copy_path = [
            sysconfig.get_path('include'),
            sysconfig.get_path('platinclude'),
        ]
        libpl = sysconfig.get_config_var('LIBPL')
        if libpl is None:
            """
            if os.name != 'nt':
                if sys.version_info[0] == 2:
                    assert sys.subversion[0] == 'PyPy'  # not available in Windows CPython 3
                else:
                    assert sys.implementation.name == 'pypy'  # Python 3 only
            """
        else:
            copy_path.append(libpl)

        prefix = sysconfig.get_config_var('prefix')
        assert prefix is not None

        for path in copy_path:
            assert path is not None
            if path.startswith(prefix):
                relative_path = path[len(prefix + os.pathsep) :]
                path = os.path.join(env.path, relative_path)
            assert os.path.exists(path)


@pytest.mark.isolated
def test_isolation():
    subprocess.check_call([sys.executable, '-c', 'import build.env'])
    with build.env.IsolatedEnvironment.for_current() as env:
        with pytest.raises(subprocess.CalledProcessError):
            debug = 'import sys; import os; print(os.linesep.join(sys.path));'
            subprocess.check_call([env.executable, '-c', '{} import build.env'.format(debug)])


@pytest.mark.isolated
def test_isolated_environment_setup_require_virtualenv(mocker):
    mocker.patch.dict(os.environ, {'PIP_REQUIRE_VIRTUALENV': 'true'})
    with build.env.IsolatedEnvironment.for_current():
        assert 'PIP_REQUIRE_VIRTUALENV' not in os.environ
    assert os.environ['PIP_REQUIRE_VIRTUALENV'] == 'true'


@pytest.mark.isolated
def test_isolated_environment_install(mocker):
    with build.env.IsolatedEnvironment.for_current() as env:
        mocker.patch('subprocess.check_call')

        env.install([])
        subprocess.check_call.assert_not_called()

        env.install(['some', 'requirements'])
        if sys.version_info[:2] != (3, 5):
            subprocess.check_call.assert_called()
        args = subprocess.check_call.call_args[0][0][:-1]
        assert args == [
            env._pip_executable,
            '-m',
            'pip',
            'install',
            '--prefix',
            env.path,
            '--ignore-installed',
            '--no-warn-script-location',
            '--disable-pip-version-check',
            '-r',
        ]


def test_uninitialised_isolated_environment():
    env = build.env.IsolatedEnvironment.for_current()

    with pytest.raises(RuntimeError):
        env.path


def test_create_isolated_build_host_with_no_pip(tmp_path, capfd, mocker):
    mocker.patch.object(build.env, 'pip', None)
    expected = {'pip', 'greenlet', 'readline', 'cffi'} if platform.python_implementation() == "PyPy" else {'pip'}

    with build.env.IsolatedEnvironment.for_current() as isolated_env:
        cmd = [isolated_env.executable, '-m', 'pip', 'list', '--format', 'json']
        packages = {p['name'] for p in json.loads(subprocess.check_output(cmd, universal_newlines=True))}
        assert packages == expected
    assert isolated_env._pip_executable == isolated_env.executable
    out, err = capfd.readouterr()
    assert out  # ensurepip prints onto the stdout
    assert not err


def test_create_isolated_build_has_with_pip(tmp_path, capfd, mocker):
    with build.env.IsolatedEnvironment.for_current() as isolated_env:
        pass
    assert isolated_env._pip_executable == sys.executable
    out, err = capfd.readouterr()
    assert not out
    assert not err
