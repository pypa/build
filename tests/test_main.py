# SPDX-License-Identifier: MIT

import sys
import os

import pytest

import build.__main__


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


@pytest.mark.skipif(sys.version_info[:2] == (3, 5), reason='bug in mock')
def test_build(mocker):
    def _error(*_):  # pragma: no cover
        raise SystemExit

    mocker.patch('importlib.import_module')
    mocker.patch('build.ProjectBuilder.check_depencencies')
    mocker.patch('build.ProjectBuilder.build')
    mocker.patch('build.__main__._error')

    build.ProjectBuilder.check_depencencies.side_effect = [[], ['something'], [], []]

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
