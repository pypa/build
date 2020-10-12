# SPDX-License-Identifier: MIT

import contextlib
import io
import os
import sys

import pytest

import build
import build.__main__
from build.env import Isolation

if sys.version_info >= (3,):  # pragma: no cover
    build_open_owner = 'builtins'
else:  # pragma: no cover
    build_open_owner = 'build'


cwd = os.getcwd()
out = os.path.join(cwd, 'dist')
default_isolation = Isolation()


@pytest.mark.parametrize(
    ('cli_args', 'build_args'),
    [
        (
            [],
            (cwd, out, ['sdist', 'wheel'], default_isolation, {}, False),
        ),
        (
            ['-n'],
            (cwd, out, ['sdist', 'wheel'], Isolation(enabled=False), {}, False),
        ),
        (
            ['-s'],
            (cwd, out, ['sdist'], default_isolation, {}, False),
        ),
        (
            ['-w'],
            (cwd, out, ['wheel'], default_isolation, {}, False),
        ),
        (
            ['source'],
            ('source', out, ['sdist', 'wheel'], default_isolation, {}, False),
        ),
        (
            ['-o', 'out'],
            (cwd, 'out', ['sdist', 'wheel'], default_isolation, {}, False),
        ),
        (
            ['-x'],
            (cwd, out, ['sdist', 'wheel'], default_isolation, {}, True),
        ),
        (
            ['-C--flag1', '-C--flag2'],
            (cwd, out, ['sdist', 'wheel'], default_isolation, {'--flag1': '', '--flag2': ''}, False),
        ),
        (
            ['-C--flag=value'],
            (cwd, out, ['sdist', 'wheel'], default_isolation, {'--flag': 'value'}, False),
        ),
        (
            ['-C--flag1=value', '-C--flag2=other_value', '-C--flag2=extra_value'],
            (
                cwd,
                out,
                ['sdist', 'wheel'],
                default_isolation,
                {'--flag1': 'value', '--flag2': ['other_value', 'extra_value']},
                False,
            ),
        ),
        (['--ensurepip'], (cwd, out, ['sdist', 'wheel'], Isolation(ensure_pip=True), {}, False)),
        (['--cache', 'demo'], (cwd, out, ['sdist', 'wheel'], Isolation(cache='demo'), {}, False)),
        (['--reset-cache'], (cwd, out, ['sdist', 'wheel'], Isolation(reset_cache=True), {}, False)),
    ],
)
def test_parse_args(mocker, cli_args, build_args):
    build_cmd = mocker.patch('build.__main__.build')

    build.__main__.main(cli_args)
    build_cmd.assert_called_once()
    args, kwargs = build_cmd.call_args
    assert not kwargs
    assert args == build_args


def test_prog():
    out = io.StringIO()

    if sys.version_info >= (3,):  # pragma: no cover
        with pytest.raises(SystemExit):
            with contextlib.redirect_stdout(out):
                build.__main__.main(['--help'], prog='something')

        assert out.getvalue().startswith('usage: something [-h]')
    else:  # pragma: no cover
        with pytest.raises(SystemExit):
            build.__main__.main(['--help'], prog='something')


@pytest.mark.isolated
def test_build(mocker, test_flit_path):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('build.ProjectBuilder.check_dependencies')
    mocker.patch('build.ProjectBuilder.build')
    mocker.patch('build.__main__._error')
    mocker.patch('build.env.IsolatedEnvironment.install')

    build.ProjectBuilder.check_dependencies.side_effect = [[], ['something'], [], []]
    build.env.IsolatedEnvironment._path = mocker.Mock()

    # isolation=True
    build.__main__.build(test_flit_path, '.', ['sdist'], Isolation())
    build.ProjectBuilder.build.assert_called_with('sdist', '.')

    # check_dependencies = []
    build.__main__.build(test_flit_path, '.', ['sdist'], Isolation(enabled=False))
    build.ProjectBuilder.build.assert_called_with('sdist', '.')
    build.env.IsolatedEnvironment.install.assert_called_with({'flit_core >=2,<3'})

    # check_dependencies = ['something']
    build.__main__.build(test_flit_path, '.', ['sdist'], Isolation(enabled=False))
    build.ProjectBuilder.build.assert_called_with('sdist', '.')
    build.__main__._error.assert_called_with('Missing dependencies:\n\tsomething')

    build.ProjectBuilder.build.side_effect = [build.BuildException, build.BuildBackendException]
    build.__main__._error.reset_mock()

    # BuildException
    build.__main__.build(test_flit_path, '.', ['sdist'], Isolation())
    build.__main__._error.assert_called_with('')

    build.__main__._error.reset_mock()

    # BuildBackendException
    build.__main__.build(test_flit_path, '.', ['sdist'], Isolation())
    build.__main__._error.assert_called_with('')
