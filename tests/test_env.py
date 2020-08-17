# SPDX-License-Identifier: MIT

import os
import subprocess
import sys
import sysconfig

import build.env


def test_isolated_environment_setup(mocker):
    old_path = os.environ['PATH']
    with build.env.IsolatedEnvironment() as env:
        if os.name != 'nt':
            assert os.environ['PATH'] == os.pathsep.join([os.path.join(env._path, 'bin'), old_path])
        assert os.environ['PYTHONHOME'] == env._path

        python_path = os.environ['PYTHONPATH'].split(os.pathsep)
        for path in ('purelib', 'platlib'):
            assert sysconfig.get_path(path) not in python_path
            assert sysconfig.get_path(
                path,
                vars={
                    'base': env._path,
                    'platbase': env._path,
                }
            ) in python_path

        copy_path = (
            sysconfig.get_path('include'),
            sysconfig.get_path('platinclude'),
            sysconfig.get_config_var('LIBPL'),
        )

        prefix = sysconfig.get_config_var('prefix')
        assert prefix is not None

        for path in copy_path:
            assert path is not None
            if path.startswith(prefix):
                relative_path = path[len(prefix + os.pathsep):]
                path = os.path.join(env._path, relative_path)
            assert os.path.exists(path)


def test_isolated_environment_install(mocker):
    with build.env.IsolatedEnvironment() as env:
        mocker.patch('subprocess.check_call')

        env.install([])
        subprocess.check_call.assert_not_called()

        env.install(['some', 'requirements'])
        if sys.version_info[:2] != (3, 5):
            subprocess.check_call.assert_called()
        assert subprocess.check_call.call_args[0][0] == [
            sys.executable, '-m', 'pip', 'install', '--ignore-installed', '--prefix', env._path, 'some', 'requirements'
        ]
