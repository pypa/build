# SPDX-License-Identifier: MIT

import contextlib
import io
import os
import re
import subprocess
import sys
import venv

import pytest

import build
import build.__main__


pytestmark = pytest.mark.contextvars


build_open_owner = 'builtins'

cwd = os.getcwd()
out = os.path.join(cwd, 'dist')

ANSI_STRIP = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


@pytest.mark.parametrize(
    ('cli_args', 'build_args', 'hook'),
    [
        (
            [],
            [cwd, out, ['wheel'], {}, True, False, None],
            'build_package_via_sdist',
        ),
        (
            ['-n'],
            [cwd, out, ['wheel'], {}, False, False, None],
            'build_package_via_sdist',
        ),
        (
            ['-s'],
            [cwd, out, ['sdist'], {}, True, False, None],
            'build_package',
        ),
        (
            ['-w'],
            [cwd, out, ['wheel'], {}, True, False, None],
            'build_package',
        ),
        (
            ['-s', '-w'],
            [cwd, out, ['sdist', 'wheel'], {}, True, False, None],
            'build_package',
        ),
        (
            ['source'],
            ['source', os.path.join('source', 'dist'), ['wheel'], {}, True, False, None],
            'build_package_via_sdist',
        ),
        (
            ['-o', 'out'],
            [cwd, 'out', ['wheel'], {}, True, False, None],
            'build_package_via_sdist',
        ),
        (
            ['source', '-o', 'out'],
            ['source', 'out', ['wheel'], {}, True, False, None],
            'build_package_via_sdist',
        ),
        (
            ['-x'],
            [cwd, out, ['wheel'], {}, True, True, None],
            'build_package_via_sdist',
        ),
        (
            ['--installer', 'uv'],
            [cwd, out, ['wheel'], {}, True, False, 'uv'],
            'build_package_via_sdist',
        ),
        (
            ['-C--flag1', '-C--flag2'],
            [cwd, out, ['wheel'], {'--flag1': '', '--flag2': ''}, True, False, None],
            'build_package_via_sdist',
        ),
        (
            ['-C--flag=value'],
            [cwd, out, ['wheel'], {'--flag': 'value'}, True, False, None],
            'build_package_via_sdist',
        ),
        (
            ['-C--flag1=value', '-C--flag2=other_value', '-C--flag2=extra_value'],
            [cwd, out, ['wheel'], {'--flag1': 'value', '--flag2': ['other_value', 'extra_value']}, True, False, None],
            'build_package_via_sdist',
        ),
        (
            ['--config-json={"one": 1, "two": [2, 3], "three": {"in": "out"}}'],
            [cwd, out, ['wheel'], {'one': 1, 'two': [2, 3], 'three': {'in': 'out'}}, True, False, None],
            'build_package_via_sdist',
        ),
        (
            ['--config-json', '{"outer": {"inner": {"deeper": 2}}}'],
            [cwd, out, ['wheel'], {'outer': {'inner': {'deeper': 2}}}, True, False, None],
            'build_package_via_sdist',
        ),
        (
            ['--config-json', '{}'],
            [cwd, out, ['wheel'], {}, True, False, None],
            'build_package_via_sdist',
        ),
    ],
)
def test_parse_args(mocker, cli_args, build_args, hook):
    build_package = mocker.patch('build.__main__.build_package', return_value=['something'])
    build_package_via_sdist = mocker.patch('build.__main__.build_package_via_sdist', return_value=['something'])

    build.__main__.main(cli_args)

    if hook == 'build_package':
        build_package.assert_called_with(*build_args)
    elif hook == 'build_package_via_sdist':
        build_package_via_sdist.assert_called_with(*build_args)
    else:  # pragma: no cover
        msg = f'Unknown hook {hook}'
        raise ValueError(msg)


def test_prog():
    out = io.StringIO()

    with pytest.raises(SystemExit):
        with contextlib.redirect_stdout(out):
            build.__main__.main(['--help'], prog='something')

    assert out.getvalue().startswith('usage: something [-h]')


def test_version(capsys):
    with pytest.raises(SystemExit):
        build.__main__.main(['--version'])
    out, err = capsys.readouterr()
    assert out.startswith(f'build {build.__version__}')


@pytest.mark.isolated
def test_build_isolated(mocker, package_test_flit):
    build_cmd = mocker.patch('build.ProjectBuilder.build', return_value='something')
    required_cmd = mocker.patch(
        'build.ProjectBuilder.get_requires_for_build',
        side_effect=[
            ['dep1', 'dep2'],
        ],
    )
    mocker.patch('build.__main__._error')
    install = mocker.patch('build.env.DefaultIsolatedEnv.install')

    build.__main__.build_package(package_test_flit, '.', ['sdist'])

    install.assert_any_call({'flit_core >=2,<4'})

    required_cmd.assert_called_with('sdist', {})
    install.assert_any_call(['dep1', 'dep2'])

    build_cmd.assert_called_with('sdist', '.', {})


def test_build_no_isolation_check_deps_empty(mocker, package_test_flit):
    # check_dependencies = []
    build_cmd = mocker.patch('build.ProjectBuilder.build', return_value='something')
    mocker.patch('build.ProjectBuilder.check_dependencies', return_value=[])

    build.__main__.build_package(package_test_flit, '.', ['sdist'], isolation=False)

    build_cmd.assert_called_with('sdist', '.', {})


@pytest.mark.parametrize(
    ['missing_deps', 'output'],
    [
        ([('foo',)], '\n\tfoo'),
        ([('foo',), ('bar', 'baz', 'qux')], '\n\tfoo\n\tbar\n\tbaz -> qux'),
    ],
)
def test_build_no_isolation_with_check_deps(mocker, package_test_flit, missing_deps, output):
    error = mocker.patch('build.__main__._error')
    build_cmd = mocker.patch('build.ProjectBuilder.build', return_value='something')
    mocker.patch('build.ProjectBuilder.check_dependencies', return_value=missing_deps)

    build.__main__.build_package(package_test_flit, '.', ['sdist'], isolation=False)

    build_cmd.assert_called_with('sdist', '.', {})
    error.assert_called_with('Missing dependencies:' + output)


@pytest.mark.parametrize(
    ['cli_args', 'err_msg'],
    [
        (['-Cone=1', '--config-json={"two": 2}'], 'not allowed with argument'),
        (['--config-json={"two": 2'], 'Invalid JSON in --config-json'),
        (['--config-json=[1]'], '--config-json must contain a JSON object'),
    ],
)
def test_config_json_errors(cli_args, err_msg, capsys):
    with pytest.raises(SystemExit):
        build.__main__.main(cli_args)

    outerr = capsys.readouterr()
    assert err_msg in outerr.out or err_msg in outerr.err


@pytest.mark.isolated
def test_build_raises_build_exception(mocker, package_test_flit):
    mocker.patch('build.ProjectBuilder.get_requires_for_build', side_effect=build.BuildException)
    mocker.patch('build.env.DefaultIsolatedEnv.install')

    with pytest.raises(build.BuildException):
        build.__main__.build_package(package_test_flit, '.', ['sdist'])


@pytest.mark.isolated
def test_build_raises_build_backend_exception(mocker, package_test_flit):
    mocker.patch('build.ProjectBuilder.get_requires_for_build', side_effect=build.BuildBackendException(Exception('a')))
    mocker.patch('build.env.DefaultIsolatedEnv.install')

    msg = f"Backend operation failed: Exception('a'{',' if sys.version_info < (3, 7) else ''})"
    with pytest.raises(build.BuildBackendException, match=re.escape(msg)):
        build.__main__.build_package(package_test_flit, '.', ['sdist'])


@pytest.mark.network
@pytest.mark.pypy3323bug
def test_build_package(tmp_dir, package_test_setuptools):
    build.__main__.build_package(package_test_setuptools, tmp_dir, ['sdist', 'wheel'])

    assert sorted(os.listdir(tmp_dir)) == [
        'test_setuptools-1.0.0-py3-none-any.whl',
        'test_setuptools-1.0.0.tar.gz',
    ]


@pytest.mark.network
@pytest.mark.pypy3323bug
def test_build_package_via_sdist(tmp_dir, package_test_setuptools):
    build.__main__.build_package_via_sdist(package_test_setuptools, tmp_dir, ['wheel'])

    assert sorted(os.listdir(tmp_dir)) == [
        'test_setuptools-1.0.0-py3-none-any.whl',
        'test_setuptools-1.0.0.tar.gz',
    ]


@pytest.mark.pypy3323bug
def test_build_package_via_sdist_cant_build(tmp_dir, package_test_cant_build_via_sdist):
    with pytest.raises(build.BuildBackendException):
        build.__main__.build_package_via_sdist(package_test_cant_build_via_sdist, tmp_dir, ['wheel'])


def test_build_package_via_sdist_invalid_distribution(tmp_dir, package_test_setuptools):
    with pytest.raises(ValueError, match='Only binary distributions are allowed but sdist was specified'):
        build.__main__.build_package_via_sdist(package_test_setuptools, tmp_dir, ['sdist'])


@pytest.mark.pypy3323bug
@pytest.mark.parametrize(
    ('args', 'output'),
    [
        pytest.param(
            [],
            [
                '* Creating isolated environment: venv+pip...',
                '* Installing packages in isolated environment:',
                '  - setuptools >= 42.0.0',
                '* Getting build dependencies for sdist...',
                '* Building sdist...',
                '* Building wheel from sdist',
                '* Creating isolated environment: venv+pip...',
                '* Installing packages in isolated environment:',
                '  - setuptools >= 42.0.0',
                '* Getting build dependencies for wheel...',
                '* Building wheel...',
                'Successfully built test_setuptools-1.0.0.tar.gz and test_setuptools-1.0.0-py3-none-any.whl',
            ],
            id='via-sdist-isolation',
            marks=[pytest.mark.network, pytest.mark.isolated],
        ),
        pytest.param(
            ['--no-isolation'],
            [
                '* Getting build dependencies for sdist...',
                '* Building sdist...',
                '* Building wheel from sdist',
                '* Getting build dependencies for wheel...',
                '* Building wheel...',
                'Successfully built test_setuptools-1.0.0.tar.gz and test_setuptools-1.0.0-py3-none-any.whl',
            ],
            id='via-sdist-no-isolation',
        ),
        pytest.param(
            ['--wheel'],
            [
                '* Creating isolated environment: venv+pip...',
                '* Installing packages in isolated environment:',
                '  - setuptools >= 42.0.0',
                '* Getting build dependencies for wheel...',
                '* Building wheel...',
                'Successfully built test_setuptools-1.0.0-py3-none-any.whl',
            ],
            id='wheel-direct-isolation',
            marks=[pytest.mark.network, pytest.mark.isolated],
        ),
        pytest.param(
            ['--wheel', '--no-isolation'],
            [
                '* Getting build dependencies for wheel...',
                '* Building wheel...',
                'Successfully built test_setuptools-1.0.0-py3-none-any.whl',
            ],
            id='wheel-direct-no-isolation',
        ),
        pytest.param(
            ['--sdist', '--no-isolation'],
            [
                '* Getting build dependencies for sdist...',
                '* Building sdist...',
                'Successfully built test_setuptools-1.0.0.tar.gz',
            ],
            id='sdist-direct-no-isolation',
        ),
        pytest.param(
            ['--sdist', '--wheel', '--no-isolation'],
            [
                '* Getting build dependencies for sdist...',
                '* Building sdist...',
                '* Getting build dependencies for wheel...',
                '* Building wheel...',
                'Successfully built test_setuptools-1.0.0.tar.gz and test_setuptools-1.0.0-py3-none-any.whl',
            ],
            id='sdist-and-wheel-direct-no-isolation',
        ),
    ],
)
@pytest.mark.flaky(reruns=5)
def test_output(package_test_setuptools, tmp_dir, capsys, args, output):
    build.__main__.main([package_test_setuptools, '-o', tmp_dir, *args])
    stdout, stderr = capsys.readouterr()
    assert set(stdout.splitlines()) <= set(output)


@pytest.mark.pypy3323bug
@pytest.mark.parametrize(
    ('color', 'stdout_error', 'stdout_body'),
    [
        (
            False,
            'ERROR ',
            [
                '* Creating isolated environment: venv+pip...',
                '* Installing packages in isolated environment:',
                '  - setuptools >= 42.0.0',
                '  - this is invalid',
            ],
        ),
        (
            True,
            '\33[91mERROR\33[0m ',
            [
                '\33[1m* Creating isolated environment: venv+pip...\33[0m',
                '\33[1m* Installing packages in isolated environment:\33[0m',
                '  - setuptools >= 42.0.0',
                '  - this is invalid',
            ],
        ),
    ],
    ids=['no-color', 'color'],
)
@pytest.mark.usefixtures('local_pip')
def test_output_env_subprocess_error(
    mocker,
    monkeypatch,
    package_test_invalid_requirements,
    tmp_dir,
    capsys,
    color,
    stdout_body,
    stdout_error,
):
    try:
        # do not inject hook to have clear output on capsys
        mocker.patch('colorama.init')
    except ModuleNotFoundError:  # colorama might not be available
        pass

    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.setenv('FORCE_COLOR' if color else 'NO_COLOR', '')

    with pytest.raises(SystemExit):
        build.__main__.main([package_test_invalid_requirements, '-o', tmp_dir])
    stdout, stderr = capsys.readouterr()
    stdout, stderr = stdout.splitlines(), stderr.splitlines()

    assert stdout[:4] == stdout_body
    assert stdout[-1].startswith(stdout_error)

    # Newer versions of pip also color stderr - strip them if present
    cleaned_stderr = ANSI_STRIP.sub('', '\n'.join(stderr)).strip()
    assert cleaned_stderr.startswith('< ERROR: Invalid requirement: ')


@pytest.mark.parametrize(
    ('tty', 'env', 'colors'),
    [
        (False, {}, build.__main__._NO_COLORS),
        (True, {}, build.__main__._COLORS),
        (False, {'NO_COLOR': ''}, build.__main__._NO_COLORS),
        (True, {'NO_COLOR': ''}, build.__main__._NO_COLORS),
        (False, {'FORCE_COLOR': ''}, build.__main__._COLORS),
        (True, {'FORCE_COLOR': ''}, build.__main__._COLORS),
    ],
)
def test_colors(mocker, monkeypatch, tty, env, colors):
    mocker.patch('sys.stdout.isatty', return_value=tty)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    build.__main__._init_colors()

    assert build.__main__._styles.get() == colors


def test_colors_conflict(monkeypatch):
    with monkeypatch.context() as m:
        m.setenv('NO_COLOR', '')
        m.setenv('FORCE_COLOR', '')

        with pytest.warns(
            UserWarning,
            match='Both NO_COLOR and FORCE_COLOR environment variables are set, disabling color',
        ):
            build.__main__._init_colors()

        assert build.__main__._styles.get() == build.__main__._NO_COLORS


def test_venv_fail(monkeypatch, package_test_flit, tmp_dir, capsys):
    def raise_called_process_err(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ['test', 'args'], b'stdoutput', b'stderror')

    monkeypatch.setattr(venv.EnvBuilder, 'create', raise_called_process_err)
    monkeypatch.setenv('NO_COLOR', '')

    with pytest.raises(SystemExit):
        build.__main__.main([package_test_flit, '-o', tmp_dir])

    stdout, stderr = capsys.readouterr()

    assert (
        stdout
        == """\
* Creating isolated environment: venv+pip...
> test args
< stdoutput
ERROR Failed to create venv. Maybe try installing virtualenv.
"""
    )
    assert (
        stderr
        == """\
< stderror
"""
    )


@pytest.mark.network
@pytest.mark.parametrize('verbosity', [0, 1])
def test_verbose_output(
    capsys: pytest.CaptureFixture,
    monkeypatch,
    tmp_dir,
    package_test_flit,
    verbosity: int,
):
    monkeypatch.setenv('NO_COLOR', '')

    cmd = [package_test_flit, '-w', '-o', tmp_dir]
    if verbosity:
        cmd.insert(0, f'-{"v" * verbosity}')

    build.__main__.main(cmd)

    stdout = capsys.readouterr().out.splitlines()
    assert sum(1 for o in stdout if o.startswith('> ')) == verbosity
