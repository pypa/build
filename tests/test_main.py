# SPDX-License-Identifier: MIT

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
