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
        (
            [],
            [cwd, out, ['sdist', 'wheel'], {}, True, False],
        ),
        (
            ['-n'],
            [cwd, out, ['sdist', 'wheel'], {}, False, False],
        ),
        (
            ['-s'],
            [cwd, out, ['sdist'], {}, True, False],
        ),
        (
            ['-w'],
            [cwd, out, ['wheel'], {}, True, False],
        ),
        (
            ['source'],
            ['source', out, ['sdist', 'wheel'], {}, True, False],
        ),
        (
            ['-o', 'out'],
            [cwd, 'out', ['sdist', 'wheel'], {}, True, False],
        ),
        (
            ['-x'],
            [cwd, out, ['sdist', 'wheel'], {}, True, True],
        ),
        (
            ['-C--flag1', '-C--flag2'],
            [cwd, out, ['sdist', 'wheel'], {'--flag1': '', '--flag2': ''}, True, False],
        ),
        (
            ['-C--flag=value'],
            [cwd, out, ['sdist', 'wheel'], {'--flag': 'value'}, True, False],
        ),
        (
            ['-C--flag1=value', '-C--flag2=other_value', '-C--flag2=extra_value'],
            [cwd, out, ['sdist', 'wheel'], {'--flag1': 'value', '--flag2': ['other_value', 'extra_value']}, True, False],
        ),
    ],
)
def test_parse_args(mocker, cli_args, build_args):
    mocker.patch('build.__main__.build_package')

    build.__main__.main(cli_args)
    build.__main__.build_package.assert_called_with(*build_args)


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


def test_version(capsys):
    with pytest.raises(SystemExit):
        build.__main__.main(['--version'])
    out, err = capsys.readouterr()
    target = out if sys.version_info[0] == 3 else err
    assert target.startswith('build {}'.format(build.__version__))


@pytest.mark.isolated
def test_build_isolated(mocker, test_flit_path):
    build_cmd = mocker.patch('build.ProjectBuilder.build')
    mocker.patch('build.__main__._error')
    install = mocker.patch('build.env._IsolatedEnvVenvPip.install')

    build.__main__.build_package(test_flit_path, '.', ['sdist'])

    build_cmd.assert_called_with('sdist', '.')
    install.assert_called_with({'flit_core >=2,<3'})


def test_build_no_isolation_check_deps_empty(mocker, test_flit_path):
    # check_dependencies = []
    build_cmd = mocker.patch('build.ProjectBuilder.build')
    mocker.patch('build.ProjectBuilder.check_dependencies', return_value=[])

    build.__main__.build_package(test_flit_path, '.', ['sdist'], isolation=False)

    build_cmd.assert_called_with('sdist', '.')


def test_build_no_isolation_with_check_deps(mocker, test_flit_path):
    # check_dependencies = ['something']
    error = mocker.patch('build.__main__._error')
    build_cmd = mocker.patch('build.ProjectBuilder.build')
    mocker.patch('build.ProjectBuilder.check_dependencies', return_value=['something'])

    build.__main__.build_package(test_flit_path, '.', ['sdist'], isolation=False)

    build_cmd.assert_called_with('sdist', '.')
    error.assert_called_with('Missing dependencies:\n\tsomething')


@pytest.mark.isolated
def test_build_raises_build_exception(mocker, test_flit_path):
    error = mocker.patch('build.__main__._error')
    mocker.patch('build.ProjectBuilder.build', side_effect=build.BuildException)
    mocker.patch('build.env._IsolatedEnvVenvPip.install')

    build.__main__.build_package(test_flit_path, '.', ['sdist'])

    error.assert_called_with('')


@pytest.mark.isolated
def test_build_raises_build_backend_exception(mocker, test_flit_path):
    error = mocker.patch('build.__main__._error')
    mocker.patch('build.ProjectBuilder.build', side_effect=build.BuildBackendException)
    mocker.patch('build.env._IsolatedEnvVenvPip.install')

    build.__main__.build_package(test_flit_path, '.', ['sdist'])

    error.assert_called_with('')
