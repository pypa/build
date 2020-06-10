# SPDX-License-Identifier: MIT

import sys
import os

import pytest

import casei.__main__


if sys.version_info >= (3,):  # pragma: no cover
    build_open_owner = 'builtins'
else:  # pragma: no cover
    build_open_owner = 'casei'


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
    mocker.patch('casei.__main__.build')

    casei.__main__.main(cli_args)
    casei.__main__.build.assert_called_with(*build_args)


@pytest.mark.skipif(sys.version_info[:2] == (3, 5), reason='bug in mock')
def test_build(mocker):
    open_mock = mocker.mock_open(read_data='')
    mocker.patch('{}.open'.format(build_open_owner), open_mock)
    mocker.patch('importlib.import_module')
    mocker.patch('casei.ProjectBuilder.check_depencencies')
    mocker.patch('casei.ProjectBuilder.build')
    mocker.patch('casei.__main__._error')

    casei.ProjectBuilder.check_depencencies.side_effect = [[], ['something'], [], []]

    # check_dependencies = []
    casei.__main__.build('.', '.', ['sdist'])
    casei.ProjectBuilder.build.assert_called()

    # check_dependencies = ['something]
    casei.__main__.build('.', '.', ['sdist'])
    casei.__main__._error.assert_called()

    casei.ProjectBuilder.build.side_effect = [
        casei.BuildException,
        casei.BuildBackendException
    ]
    casei.__main__._error.reset_mock()

    # BuildException
    casei.__main__.build('.', '.', ['sdist'])
    casei.__main__._error.assert_called()

    casei.__main__._error.reset_mock()

    # BuildBackendException
    casei.__main__.build('.', '.', ['sdist'])
    casei.__main__._error.assert_called()
