# SPDX-License-Identifier: MIT

import contextlib
import io
import sys
import os

import pytest

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
        ([], [cwd, out, ['sdist', 'wheel'], False]),
        (['-s'], [cwd, out, ['sdist'], False]),
        (['-w'], [cwd, out, ['wheel'], False]),
        (['source'], ['source', out, ['sdist', 'wheel'], False]),
        (['-o', 'out'], [cwd, 'out', ['sdist', 'wheel'], False]),
        (['-x'], [cwd, out, ['sdist', 'wheel'], True]),
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


@pytest.mark.skipif(sys.version_info[:2] == (3, 5), reason='bug in mock')
def test_build(mocker):
    open_mock = mocker.mock_open(read_data='')
    mocker.patch('{}.open'.format(build_open_owner), open_mock)
    mocker.patch('importlib.import_module')
    mocker.patch('build.ProjectBuilder.check_dependencies')
    mocker.patch('build.ProjectBuilder.build')
    mocker.patch('build.__main__._error')

    build.ProjectBuilder.check_dependencies.side_effect = [[], ['something'], [], []]

    # check_dependencies = []
    build.__main__.build('.', '.', ['sdist'])
    build.ProjectBuilder.build.assert_called()

    # check_dependencies = ['something]
    build.__main__.build('.', '.', ['sdist'])
    build.__main__._error.assert_called()

    build.ProjectBuilder.build.side_effect = [build.BuildException, build.BuildBackendException]
    build.__main__._error.reset_mock()

    # BuildException
    build.__main__.build('.', '.', ['sdist'])
    build.__main__._error.assert_called()

    build.__main__._error.reset_mock()

    # BuildBackendException
    build.__main__.build('.', '.', ['sdist'])
    build.__main__._error.assert_called()
