# SPDX-License-Identifier: MIT

import os
import os.path
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


def test_isolation():
    subprocess.check_call([sys.executable, '-c', 'import build.env'])
    with build.env.IsolatedEnvironment.for_current() as env:
        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_call([env.executable, '-c', 'import build.env'])


def test_isolated_environment_setup_require_virtualenv(mocker):
    mocker.patch.dict(os.environ, {'PIP_REQUIRE_VIRTUALENV': 'true'})
    with build.env.IsolatedEnvironment.for_current():
        assert 'PIP_REQUIRE_VIRTUALENV' not in os.environ
    assert os.environ['PIP_REQUIRE_VIRTUALENV'] == 'true'


def test_isolated_environment_install(mocker):
    with build.env.IsolatedEnvironment.for_current() as env:
        mocker.patch('subprocess.check_call')

        env.install([])
        subprocess.check_call.assert_not_called()

        env.install(['some', 'requirements'])
        if sys.version_info[:2] != (3, 5):
            subprocess.check_call.assert_called()
        args = subprocess.check_call.call_args[0][0]
        assert args[:7] == [env.executable, '-m', 'pip', 'install', '--prefix', env.path, '-r']


def test_uninitialised_isolated_environment():
    env = build.env.IsolatedEnvironment.for_current()

    with pytest.raises(RuntimeError):
        env.path
