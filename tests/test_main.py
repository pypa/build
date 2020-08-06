# SPDX-License-Identifier: MIT

import contextlib
import io
import os
import sys

import pytest

import build
import build.__main__


if sys.version_info >= (3,):  # pragma: no cover
    build_open_owner = 'builtins'
else:  # pragma: no cover
    build_open_owner = 'build'


cwd = os.getcwd()
out = os.path.join(cwd, 'dist')


@pytest.mark.parametrize(
    ('cli_args', 'build_args'),
    [
        ([], [cwd, out, ['sdist', 'wheel'], {}, True, False]),
        (['-n'], [cwd, out, ['sdist', 'wheel'], {}, False, False]),
        (['-s'], [cwd, out, ['sdist'], {}, True, False]),
        (['-w'], [cwd, out, ['wheel'], {}, True, False]),
        (['source'], ['source', out, ['sdist', 'wheel'], {}, True, False]),
        (['-o', 'out'], [cwd, 'out', ['sdist', 'wheel'], {}, True, False]),
        (['-x'], [cwd, out, ['sdist', 'wheel'], {}, True, True]),
        (
            ['-C--flag1', '-C--flag2'],
            [cwd, out, ['sdist', 'wheel'], {
                '--flag1': '',
                '--flag2': '',
            }, True, False]
        ),
        (
            ['-C--flag=value'],
            [cwd, out, ['sdist', 'wheel'], {
                '--flag': 'value',
            }, True, False]
        ),
        (
            ['-C--flag1=value', '-C--flag2=other_value', '-C--flag2=extra_value'],
            [cwd, out, ['sdist', 'wheel'], {
                '--flag1': 'value',
                '--flag2': ['other_value', 'extra_value'],
            }, True, False]
        ),
    ]
)
def test_parse_args(mocker, cli_args, build_args):
    mocker.patch('build.__main__.build')

    build.__main__.main(cli_args)
    build.__main__.build.assert_called_with(*build_args)


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


def test_build(mocker, test_flit_path):
    mocker.patch('importlib.import_module')
    mocker.patch('build.ProjectBuilder.check_dependencies')
    mocker.patch('build.ProjectBuilder.build')
    mocker.patch('build.__main__._error')
    mocker.patch('build.env.IsolatedEnvironment.install')

    build.ProjectBuilder.check_dependencies.side_effect = [[], ['something'], [], []]
    build.env.IsolatedEnvironment._path = mocker.Mock()

    # isolation=True
    build.__main__.build(test_flit_path, '.', ['sdist'])
    build.ProjectBuilder.build.assert_called_with('sdist', '.')

    # check_dependencies = []
    build.__main__.build(test_flit_path, '.', ['sdist'], isolation=False)
    build.ProjectBuilder.build.assert_called_with('sdist', '.')
    build.env.IsolatedEnvironment.install.assert_called_with({'flit_core >=2,<3'})

    # check_dependencies = ['something']
    build.__main__.build(test_flit_path, '.', ['sdist'], isolation=False)
    build.ProjectBuilder.build.assert_called_with('sdist', '.')
    build.__main__._error.assert_called_with('Missing dependencies:\n\tsomething')

    build.ProjectBuilder.build.side_effect = [build.BuildException, build.BuildBackendException]
    build.__main__._error.reset_mock()

    # BuildException
    build.__main__.build(test_flit_path, '.', ['sdist'])
    build.__main__._error.assert_called_with('')

    build.__main__._error.reset_mock()

    # BuildBackendException
    build.__main__.build(test_flit_path, '.', ['sdist'])
    build.__main__._error.assert_called_with('')
