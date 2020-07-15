# SPDX-License-Identifier: MIT

import os
import subprocess
import sys
import sysconfig

import build.env


def test_isolated_environment(mocker):
    old_path = os.environ['PATH']
    with build.env.IsolatedEnvironment() as env:
        if os.name != 'nt':
            assert os.environ['PATH'] == os.pathsep.join([os.path.join(env._path, 'bin'), old_path])
        assert os.environ['PYTHONHOME'] == env._path

        for path in ('purelib', 'platlib'):
            assert sysconfig.get_path(path) not in os.environ['PYTHONPATH'].split(os.pathsep)

        mocker.patch('subprocess.check_call')

        env.install([])
        subprocess.check_call.assert_not_called()

        env.install(['some', 'requirements'])
        if sys.version_info[:2] != (3, 5):
            subprocess.check_call.assert_called()
        assert subprocess.check_call.call_args[0][0] == [
            sys.executable, '-m', 'pip', 'install', '--ignore-installed', '--prefix', env._path, 'some', 'requirements'
        ]
