# SPDX-License-Identifier: MIT

from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tarfile
import unittest.mock
import venv

from collections.abc import Callable
from typing import Any

import pytest
import pytest_mock

import build
import build.__main__


pytestmark = pytest.mark.contextvars


build_open_owner = 'builtins'

cwd = os.getcwd()
out = os.path.join(cwd, 'dist')

ANSI_STRIP = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


@pytest.mark.parametrize(
    ('cli_args', 'build_args', 'build_kwargs', 'hook'),
    [
        (
            [],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['-n'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': False,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['-s'],
            (cwd, out),
            {
                'distributions': ['sdist'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package',
        ),
        (
            ['-w'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package',
        ),
        (
            ['-s', '-w'],
            (cwd, out),
            {
                'distributions': ['sdist', 'wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package',
        ),
        (
            ['source'],
            ('source', os.path.join('source', 'dist')),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['-o', 'out'],
            (cwd, 'out'),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['source', '-o', 'out'],
            ('source', 'out'),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['-x'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': True,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['--installer', 'uv'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': 'uv',
            },
            'build_package_via_sdist',
        ),
        (
            ['-C--flag1', '-C--flag2'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {'--flag1': '', '--flag2': ''},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['-C--flag=value'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {'--flag': 'value'},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['-C--flag1=value', '-C--flag2=other_value', '-C--flag2=extra_value'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {'--flag1': 'value', '--flag2': ['other_value', 'extra_value']},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['--config-json={"one": 1, "two": [2, 3], "three": {"in": "out"}}'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {'one': 1, 'two': [2, 3], 'three': {'in': 'out'}},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['--config-json', '{"outer": {"inner": {"deeper": 2}}}'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {'outer': {'inner': {'deeper': 2}}},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['--config-json', '{}'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': None,
                'installer': None,
            },
            'build_package_via_sdist',
        ),
        (
            ['--dependency-constraints-txt', 'contraints.txt'],
            (cwd, out),
            {
                'distributions': ['wheel'],
                'config_settings': {},
                'isolation': True,
                'skip_dependency_check': False,
                'dependency_constraints_txt': 'contraints.txt',
                'installer': None,
            },
            'build_package_via_sdist',
        ),
    ],
)
def test_parse_args(
    mocker: pytest_mock.MockerFixture,
    cli_args: list[str],
    build_args: tuple[Any, Any],
    build_kwargs: dict[str, Any],
    hook: str,
) -> None:
    build_package = mocker.patch('build.__main__.build_package', return_value=['something'])
    build_package_via_sdist = mocker.patch('build.__main__.build_package_via_sdist', return_value=['something'])

    build.__main__.main(cli_args)

    if hook == 'build_package':
        build_package.assert_called_with(*build_args, **build_kwargs)
    elif hook == 'build_package_via_sdist':
        build_package_via_sdist.assert_called_with(*build_args, **build_kwargs)
    else:  # pragma: no cover
        msg = f'Unknown hook {hook}'
        raise ValueError(msg)


def test_prog() -> None:
    out = io.StringIO()

    with pytest.raises(SystemExit), contextlib.redirect_stdout(out):
        build.__main__.main(['--help'], prog='something')

    assert out.getvalue().startswith('usage: something [-h]')


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        build.__main__.main(['--version'])
    out, _ = capsys.readouterr()
    assert out.startswith(f'build {build.__version__}')


@pytest.mark.isolated
def test_build_isolated(mocker: pytest_mock.MockerFixture, package_test_flit: str) -> None:
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

    install.assert_any_call({'flit_core >=2,<4'}, _fresh=True)

    required_cmd.assert_called_with('sdist', None)
    install.assert_any_call(['dep1', 'dep2'])

    build_cmd.assert_called_with('sdist', '.', None)


def test_build_no_isolation_check_deps_empty(mocker: pytest_mock.MockerFixture, package_test_flit: str) -> None:
    # check_dependencies = []
    build_cmd = mocker.patch('build.ProjectBuilder.build', return_value='something')
    mocker.patch('build.ProjectBuilder.check_dependencies', return_value=[])

    build.__main__.build_package(package_test_flit, '.', ['sdist'], isolation=False)

    build_cmd.assert_called_with('sdist', '.', None)


def test_build_package_passes_config_settings_to_build(mocker: pytest_mock.MockerFixture, package_test_flit: str) -> None:
    build_cmd = mocker.patch(
        'build.__main__._build',
        side_effect=[
            os.path.join('dist', 'test_flit-1.0.0.tar.gz'),
            os.path.join('dist', 'test_flit-1.0.0-py3-none-any.whl'),
        ],
    )
    config_settings = {'--flag': 'value'}

    built = build.__main__.build_package(
        package_test_flit,
        '.',
        ['sdist', 'wheel'],
        config_settings=config_settings,
        isolation=False,
        skip_dependency_check=True,
        dependency_constraints_txt=pathlib.Path('constraints.txt'),
        installer='uv',
    )

    assert built == ['test_flit-1.0.0.tar.gz', 'test_flit-1.0.0-py3-none-any.whl']
    build_cmd.assert_has_calls(
        [
            unittest.mock.call(
                False, package_test_flit, '.', 'sdist', config_settings, True, pathlib.Path('constraints.txt'), 'uv'
            ),
            unittest.mock.call(
                False, package_test_flit, '.', 'wheel', config_settings, True, pathlib.Path('constraints.txt'), 'uv'
            ),
        ]
    )


def test_build_package_via_sdist_passes_config_settings_to_build(mocker: pytest_mock.MockerFixture) -> None:
    build_cmd = mocker.patch(
        'build.__main__._build',
        side_effect=[
            os.path.join('dist', 'demo-1.0.0.tar.gz'),
            os.path.join('dist', 'demo-1.0.0-py3-none-any.whl'),
        ],
    )
    mocker.patch('build.__main__.tempfile.mkdtemp', return_value='temp-sdist-dir')
    mocker.patch('build.__main__.shutil.rmtree')
    tar_open = mocker.patch('build._compat.tarfile.TarFile.open')
    mocker.patch('build.__main__._ctx.log')
    config_settings = {'--flag': 'value'}

    built = build.__main__.build_package_via_sdist(
        'src',
        'dist',
        ['wheel'],
        config_settings=config_settings,
        isolation=False,
        skip_dependency_check=True,
        dependency_constraints_txt=pathlib.Path('constraints.txt'),
        installer='uv',
    )

    assert built == ['demo-1.0.0.tar.gz', 'demo-1.0.0-py3-none-any.whl']
    tar_open.return_value.__enter__.return_value.extractall.assert_called_once_with('temp-sdist-dir')
    build_cmd.assert_has_calls(
        [
            unittest.mock.call(False, 'src', 'dist', 'sdist', config_settings, True, pathlib.Path('constraints.txt'), 'uv'),
            unittest.mock.call(
                False,
                os.path.join('temp-sdist-dir', 'demo-1.0.0'),
                'dist',
                'wheel',
                config_settings,
                True,
                pathlib.Path('constraints.txt'),
                'uv',
            ),
        ]
    )
    build.__main__.shutil.rmtree.assert_called_once_with('temp-sdist-dir', ignore_errors=True)  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ('missing_deps', 'output'),
    [
        ([('foo',)], '\n\tfoo'),
        ([('foo',), ('bar', 'baz', 'qux')], '\n\tfoo\n\tbar -> baz -> qux'),
    ],
)
def test_build_no_isolation_with_check_deps(
    mocker: pytest_mock.MockerFixture, package_test_flit: str, missing_deps: list[tuple[str, ...]], output: str
) -> None:
    error = mocker.patch('build.__main__._error')
    build_cmd = mocker.patch('build.ProjectBuilder.build', return_value='something')
    mocker.patch('build.ProjectBuilder.check_dependencies', return_value=missing_deps)

    build.__main__.build_package(package_test_flit, '.', ['sdist'], isolation=False)

    build_cmd.assert_called_with('sdist', '.', None)
    error.assert_called_with('Missing dependencies:' + output)


@pytest.mark.parametrize(
    ('cli_args', 'err_msg'),
    [
        (['-Cone=1', '--config-json={"two": 2}'], 'not allowed with argument'),
        (['--config-json={"two": 2'], 'Invalid JSON in --config-json'),
        (['--config-json=[1]'], '--config-json must contain a JSON object'),
    ],
)
def test_config_json_errors(cli_args: list[str], err_msg: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        build.__main__.main(cli_args)

    outerr = capsys.readouterr()
    assert err_msg in outerr.out or err_msg in outerr.err


@pytest.mark.isolated
def test_build_raises_build_exception(mocker: pytest_mock.MockerFixture, package_test_flit: str) -> None:
    mocker.patch('build.ProjectBuilder.get_requires_for_build', side_effect=build.BuildException)
    mocker.patch('build.env.DefaultIsolatedEnv.install')

    with pytest.raises(build.BuildException):
        build.__main__.build_package(package_test_flit, '.', ['sdist'])


@pytest.mark.isolated
def test_build_raises_build_backend_exception(mocker: pytest_mock.MockerFixture, package_test_flit: str) -> None:
    mocker.patch('build.ProjectBuilder.get_requires_for_build', side_effect=build.BuildBackendException(Exception('a')))
    mocker.patch('build.env.DefaultIsolatedEnv.install')

    msg = f"Backend operation failed: Exception('a'{',' if sys.version_info < (3, 7) else ''})"
    with pytest.raises(build.BuildBackendException, match=re.escape(msg)):
        build.__main__.build_package(package_test_flit, '.', ['sdist'])


@pytest.mark.network
@pytest.mark.pypy3323bug
def test_build_package(tmp_dir: str, package_test_setuptools: str) -> None:
    build.__main__.build_package(package_test_setuptools, tmp_dir, ['sdist', 'wheel'])

    assert sorted(os.listdir(tmp_dir)) == [
        'test_setuptools-1.0.0-py3-none-any.whl',
        'test_setuptools-1.0.0.tar.gz',
    ]


@pytest.mark.network
@pytest.mark.pypy3323bug
def test_build_package_via_sdist(tmp_dir: str, package_test_setuptools: str) -> None:
    build.__main__.build_package_via_sdist(package_test_setuptools, tmp_dir, ['wheel'])

    assert sorted(os.listdir(tmp_dir)) == [
        'test_setuptools-1.0.0-py3-none-any.whl',
        'test_setuptools-1.0.0.tar.gz',
    ]


@pytest.mark.pypy3323bug
def test_build_package_via_sdist_incomplete_sdist(tmp_dir: str, package_test_cant_build_via_sdist: str) -> None:
    with pytest.raises(build.BuildBackendException):
        build.__main__.build_package_via_sdist(package_test_cant_build_via_sdist, tmp_dir, ['wheel'])


def test_build_package_via_sdist_invalid_distribution(tmp_dir: str, package_test_setuptools: str) -> None:
    with pytest.raises(ValueError, match='Only binary distributions are allowed but sdist was specified'):
        build.__main__.build_package_via_sdist(package_test_setuptools, tmp_dir, ['sdist'])


@pytest.mark.isolated
def test_build_package_with_constraints(
    mocker: pytest_mock.MockerFixture, tmp_path: pathlib.Path, package_test_flit: str
) -> None:
    install = mocker.patch('build.env.DefaultIsolatedEnv.install')

    constraints_txt_path = tmp_path.joinpath('constraints.txt')
    constraints_txt_path.write_text(
        """\
flit-core==12.34
foo==wot
""",
        encoding='utf-8',
    )

    with pytest.raises(build.BuildBackendException, match=re.escape("Backend 'flit_core.buildapi' is not available.")):
        build.__main__.build_package(package_test_flit, tmp_path, ['wheel'], dependency_constraints_txt=constraints_txt_path)

    install.assert_any_call({'flit_core >=2,<4'}, constraints={'flit-core==12.34', 'foo==wot'}, _fresh=True)


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
        pytest.param(
            ['--metadata'],
            [
                '* Creating isolated environment: venv+pip...',
                '* Getting metadata for wheel...',
                '* Getting build dependencies for wheel...',
                '* Installing packages in isolated environment:',
                '  - setuptools >= 42.0.0',
            ],
            id='metadata-isolation',
            marks=[pytest.mark.network, pytest.mark.isolated],
        ),
        pytest.param(
            ['--metadata', '--no-isolation'],
            [
                '* Getting build dependencies for wheel...',
                '* Getting metadata for wheel...',
            ],
            id='metadata-no-isolation',
        ),
    ],
)
@pytest.mark.flaky(reruns=5)
def test_logging_output(
    package_test_setuptools: str, tmp_dir: str, capsys: pytest.CaptureFixture[str], args: list[str], output: list[str]
) -> None:
    build.__main__.main([package_test_setuptools, '-o', tmp_dir, *args])
    _, stderr = capsys.readouterr()
    assert set(stderr.splitlines()) <= set(output)


@pytest.mark.pypy3323bug
@pytest.mark.parametrize(
    ('color', 'stderr_error', 'stderr_body'),
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
def test_logging_output_env_subprocess_error(
    mocker: pytest_mock.MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    package_test_invalid_requirements: str,
    tmp_dir: str,
    capsys: pytest.CaptureFixture[str],
    color: bool,
    stderr_body: list[str],
    stderr_error: str,
) -> None:
    with contextlib.suppress(ModuleNotFoundError):  # colorama might not be available
        # do not inject hook to have clear output on capsys
        mocker.patch('colorama.init')

    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.setenv('FORCE_COLOR' if color else 'NO_COLOR', '')

    with pytest.raises(SystemExit):
        build.__main__.main([package_test_invalid_requirements, '-o', tmp_dir])
    outerr = capsys.readouterr()
    stderr = outerr.err.splitlines()

    assert stderr[:4] == stderr_body
    assert stderr[-1].startswith(stderr_error)

    # Newer versions of pip also color stderr - strip them if present
    assert any(ANSI_STRIP.sub('', e).strip().startswith('< ERROR: Invalid requirement: ') for e in stderr)


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
def test_colors(
    mocker: pytest_mock.MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    tty: bool,
    env: dict[str, str],
    colors: dict[str, object],
) -> None:
    mocker.patch('sys.stdout.isatty', return_value=tty)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    build.__main__._init_colors()

    assert build.__main__._styles.get() == colors


def test_colors_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    with monkeypatch.context() as m:
        m.setenv('NO_COLOR', '')
        m.setenv('FORCE_COLOR', '')

        with pytest.warns(
            UserWarning,
            match='Both NO_COLOR and FORCE_COLOR environment variables are set, disabling color',
        ):
            build.__main__._init_colors()

        assert build.__main__._styles.get() == build.__main__._NO_COLORS


def test_logging_output_venv_failure(
    monkeypatch: pytest.MonkeyPatch, package_test_flit: str, tmp_dir: str, capsys: pytest.CaptureFixture[str]
) -> None:
    def raise_called_process_err(*_args: object, **_kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, ['test', 'args'], b'stdoutput', b'stderror')

    monkeypatch.setattr(venv.EnvBuilder, 'create', raise_called_process_err)
    monkeypatch.setenv('NO_COLOR', '')

    with pytest.raises(SystemExit):
        build.__main__.main([package_test_flit, '-o', tmp_dir])

    _, stderr = capsys.readouterr()

    assert (
        stderr
        == """\
* Creating isolated environment: venv+pip...
> test args
< stdoutput
< stderror
ERROR Failed to create venv. Maybe try installing virtualenv.
"""
    )


@pytest.mark.contextvars
@pytest.mark.network
def test_verbose_logging_output(
    subtests: Any,
    capfd: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_dir: str,
    package_test_setuptools: str,
) -> None:
    monkeypatch.setenv('NO_COLOR', '')

    no_of_lines = -1

    for verbosity in range(-2, 3):
        with subtests.test(verbosity=verbosity):
            cmd = [package_test_setuptools, '-w', '-o', tmp_dir]
            if verbosity:
                cmd.insert(0, f'-{("v" if verbosity > 0 else "q") * abs(verbosity)}')

            build.__main__.main(cmd)

            new_no_of_lines = sum(1 for s in capfd.readouterr() for i in s.splitlines())
            assert new_no_of_lines > no_of_lines
            no_of_lines = new_no_of_lines


def test_metadata_json_output(
    capsys: pytest.CaptureFixture[str],
    package_test_setuptools: str,
) -> None:
    build.__main__.main([package_test_setuptools, '--metadata', '-n'])

    stdout = capsys.readouterr().out
    metadata = json.loads(stdout)
    # Name normalised in old versions of setuptools.
    assert metadata['name'] in {'test_setuptools', 'test-setuptools'}
    assert metadata['version'] == '1.0.0'


def test_setup_cli_windows_colorama_available(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch('platform.system', return_value='Windows')
    colorama = mocker.MagicMock()
    mocker.patch.dict('sys.modules', {'colorama': colorama})
    build.__main__._setup_cli(verbosity=0)
    colorama.init.assert_called_once()


def test_setup_cli_windows_colorama_missing(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch('platform.system', return_value='Windows')
    mocker.patch.dict('sys.modules', {'colorama': None})
    build.__main__._setup_cli(verbosity=0)


def test_setup_cli_non_windows(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch('platform.system', return_value='Linux')
    build.__main__._setup_cli(verbosity=0)


def test_metadata_with_distributions_error() -> None:
    with pytest.raises(SystemExit):
        build.__main__.main(['--metadata', '--sdist'])


def test_entrypoint(mocker: pytest_mock.MockerFixture) -> None:
    main = mocker.patch('build.__main__.main')
    build.__main__.entrypoint()
    main.assert_called_once_with(sys.argv[1:])


def test_handle_build_error_build_backend_exception(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch('build.__main__._error', side_effect=SystemExit(1))

    exc = ValueError('test error')
    try:
        raise exc
    except ValueError:
        exc_info = sys.exc_info()

    with pytest.raises(SystemExit), build.__main__._handle_build_error():
        raise build.BuildBackendException(exc, exc_info=exc_info)


def test_log_unknown_kind(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch('build.__main__._cprint')
    log = build.__main__._make_logger()
    log('message', kind=('unknown',))


def test_build_no_isolation_skip_dependency_check(mocker: pytest_mock.MockerFixture, package_test_flit: str) -> None:
    build_cmd = mocker.patch('build.ProjectBuilder.build', return_value='something')
    build.__main__.build_package(package_test_flit, '.', ['sdist'], isolation=False, skip_dependency_check=True)
    build_cmd.assert_called_with('sdist', '.', None)


def test_build_package_via_sdist_empty_distributions(mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch(
        'build.__main__._build',
        return_value=os.path.join('dist', 'demo-1.0.0.tar.gz'),
    )
    result = build.__main__.build_package_via_sdist('src', 'dist', [])
    assert result == ['demo-1.0.0.tar.gz']


def test_parse_config_settings_triple_duplicate() -> None:
    result = build.__main__._parse_config_settings(['--flag=a', '--flag=b', '--flag=c'])
    assert result == {'--flag': ['a', 'b', 'c']}


def test_build_metadata_runner_without_extra_environ(
    mocker: pytest_mock.MockerFixture,
    tmp_path: pathlib.Path,
    package_test_setuptools: str,
) -> None:
    captured_runners: list[Any] = []

    @contextlib.contextmanager
    def fake_bootstrap(*_args: object, **kwargs: object) -> Any:
        captured_runners.append(kwargs['runner'])
        builder = mocker.MagicMock()
        metadata_dir = tmp_path / 'metadata'
        metadata_dir.mkdir()
        (metadata_dir / 'METADATA').write_bytes(b'Metadata-Version: 2.2\nName: test\nVersion: 1.0\n')
        builder.metadata_path.return_value = str(metadata_dir)
        yield builder

    mocker.patch('build.__main__._bootstrap_build_env', side_effect=fake_bootstrap)
    ctx_run = mocker.patch('build.__main__._ctx.run_subprocess')

    build.__main__._build_metadata(package_test_setuptools, '.', ['wheel'], isolation=False, skip_dependency_check=True)

    assert captured_runners
    captured_runners[0](['echo', 'test'])
    ctx_run.assert_called_once_with(['echo', 'test'], None, mocker.ANY)


WriteSdist = Callable[..., None]


@pytest.fixture
def write_sdist() -> WriteSdist:
    def _write(
        path: pathlib.Path,
        top_level: str,
        *,
        with_pkg_info: bool = True,
        extra: dict[str, str] | None = None,
    ) -> None:
        pkg_info = b'Metadata-Version: 2.2\nName: demo\nVersion: 1.0.0\n'
        with tarfile.open(path, 'w:gz') as tar:
            if with_pkg_info:
                info = tarfile.TarInfo(name=f'{top_level}/PKG-INFO')
                info.size = len(pkg_info)
                tar.addfile(info, io.BytesIO(pkg_info))
            body = b'[build-system]\nrequires = []\nbuild-backend = "noop"\n'
            info = tarfile.TarInfo(name=f'{top_level}/pyproject.toml')
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
            for member_name, member_body in (extra or {}).items():
                data = member_body.encode()
                info = tarfile.TarInfo(name=member_name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))

    return _write


@pytest.fixture
def sdist(tmp_path: pathlib.Path, write_sdist: WriteSdist) -> pathlib.Path:
    archive = tmp_path / 'demo-1.0.0.tar.gz'
    write_sdist(archive, 'demo-1.0.0')
    return archive


def test_validate_sdist_archive_happy(sdist: pathlib.Path) -> None:
    assert build.__main__._validate_sdist_archive(str(sdist)) == 'demo-1.0.0'


def test_validate_sdist_archive_top_level_name_mismatch(tmp_path: pathlib.Path, write_sdist: WriteSdist) -> None:
    archive = tmp_path / 'demo-1.0.0.tar.gz'
    write_sdist(archive, 'something-else-1.0')
    assert build.__main__._validate_sdist_archive(str(archive)) == 'something-else-1.0'


def _invalid_filename(tmp_path: pathlib.Path, write: WriteSdist) -> str:
    archive = tmp_path / 'noversion.tar.gz'
    write(archive, 'noversion')
    return str(archive)


def _invalid_version(tmp_path: pathlib.Path, write: WriteSdist) -> str:
    archive = tmp_path / 'demo-not_a_version.tar.gz'
    write(archive, 'demo-not_a_version')
    return str(archive)


def _corrupt_tar(tmp_path: pathlib.Path, _write: WriteSdist) -> str:
    archive = tmp_path / 'demo-1.0.0.tar.gz'
    archive.write_bytes(b'not a real tar.gz')
    return str(archive)


def _multiple_top_level(tmp_path: pathlib.Path, write: WriteSdist) -> str:
    archive = tmp_path / 'demo-1.0.0.tar.gz'
    write(archive, 'demo-1.0.0', extra={'other-1.0.0/PKG-INFO': 'x'})
    return str(archive)


def _missing_pkg_info(tmp_path: pathlib.Path, write: WriteSdist) -> str:
    archive = tmp_path / 'demo-1.0.0.tar.gz'
    write(archive, 'demo-1.0.0', with_pkg_info=False)
    return str(archive)


_REJECT_CASES: dict[str, Callable[[pathlib.Path, WriteSdist], str]] = {
    'invalid-filename': _invalid_filename,
    'invalid-version': _invalid_version,
    'corrupt-tar': _corrupt_tar,
    'multiple-top-level': _multiple_top_level,
    'missing-pkg-info': _missing_pkg_info,
}


@pytest.mark.parametrize(
    ('case', 'match'),
    [
        pytest.param('invalid-filename', 'does not look like a source distribution', id='invalid-filename'),
        pytest.param('invalid-version', 'does not look like a source distribution', id='invalid-version'),
        pytest.param('corrupt-tar', 'failed to read source distribution', id='corrupt-tar'),
        pytest.param('multiple-top-level', 'single top-level directory', id='multiple-top-level'),
        pytest.param('missing-pkg-info', 'does not contain demo-1.0.0/PKG-INFO', id='missing-pkg-info'),
    ],
)
def test_validate_sdist_archive_rejects(
    tmp_path: pathlib.Path,
    write_sdist: WriteSdist,
    case: str,
    match: str,
) -> None:
    archive = _REJECT_CASES[case](tmp_path, write_sdist)
    with pytest.raises(build.BuildException, match=match):
        build.__main__._validate_sdist_archive(archive)


def test_extract_sdist_yields_top_level(sdist: pathlib.Path) -> None:
    with build.__main__._extract_sdist(str(sdist), 'demo-1.0.0') as extracted:
        assert os.path.isdir(extracted)
        assert os.path.isfile(os.path.join(extracted, 'PKG-INFO'))
        extract_root = os.path.dirname(extracted)
    assert not os.path.exists(extract_root)


def _raise_inside_extract(sdist: pathlib.Path) -> None:
    with build.__main__._extract_sdist(str(sdist), 'demo-1.0.0') as extracted:
        msg = 'boom'
        raise RuntimeError(msg, os.path.dirname(extracted))


def test_extract_sdist_cleans_up_on_error(sdist: pathlib.Path) -> None:
    with pytest.raises(RuntimeError, match='boom') as exc_info:
        _raise_inside_extract(sdist)
    _, extract_root = exc_info.value.args
    assert not os.path.exists(extract_root)


@pytest.mark.parametrize(
    ('extra_args', 'expected_distributions', 'expected_outdir'),
    [
        pytest.param([], ['wheel'], None, id='no-flag'),
        pytest.param(['--wheel'], ['wheel'], None, id='wheel-long'),
        pytest.param(['-w'], ['wheel'], None, id='wheel-short'),
        pytest.param(['--wheel', '-o', 'custom-out'], ['wheel'], 'custom-out', id='custom-outdir'),
    ],
)
def test_main_sdist_input_wheel_dispatch(
    sdist: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
    extra_args: list[str],
    expected_distributions: list[str],
    expected_outdir: str | None,
) -> None:
    build_package = mocker.patch('build.__main__.build_package', return_value=['demo-1.0.0-py3-none-any.whl'])
    via_sdist = mocker.patch('build.__main__.build_package_via_sdist')

    build.__main__.main([str(sdist), *extra_args])

    via_sdist.assert_not_called()
    args, kwargs = build_package.call_args
    extracted_srcdir, outdir = args
    assert os.path.basename(extracted_srcdir) == 'demo-1.0.0'
    assert kwargs['distributions'] == expected_distributions
    expected = expected_outdir if expected_outdir is not None else os.path.dirname(os.path.abspath(sdist))
    assert outdir == expected


def test_main_sdist_input_metadata(sdist: pathlib.Path, mocker: pytest_mock.MockerFixture) -> None:
    build_metadata = mocker.patch('build.__main__._build_metadata', return_value=[])

    build.__main__.main([str(sdist), '--metadata'])

    args, kwargs = build_metadata.call_args
    extracted_srcdir, _outdir = args
    assert os.path.basename(extracted_srcdir) == 'demo-1.0.0'
    assert kwargs['distributions'] == ['wheel']


@pytest.mark.parametrize(
    'flags',
    [
        pytest.param(['--sdist'], id='sdist-only'),
        pytest.param(['--sdist', '--wheel'], id='sdist-and-wheel'),
    ],
)
def test_main_sdist_input_rejects_sdist_flag(
    sdist: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    flags: list[str],
) -> None:
    with pytest.raises(SystemExit):
        build.__main__.main([str(sdist), *flags])
    assert 'cannot build a source distribution from a source distribution' in capsys.readouterr().err


def test_main_sdist_input_validation_error_surfaced(
    tmp_path: pathlib.Path,
    write_sdist: WriteSdist,
    capsys: pytest.CaptureFixture[str],
) -> None:
    archive = tmp_path / 'demo-1.0.0.tar.gz'
    write_sdist(archive, 'demo-1.0.0', with_pkg_info=False)

    with pytest.raises(SystemExit):
        build.__main__.main([str(archive), '--wheel'])

    assert 'PKG-INFO' in capsys.readouterr().err


def test_main_sdist_input_passes_kwargs(sdist: pathlib.Path, mocker: pytest_mock.MockerFixture) -> None:
    build_package = mocker.patch('build.__main__.build_package', return_value=['demo-1.0.0-py3-none-any.whl'])

    build.__main__.main([str(sdist), '--wheel', '-n', '-x', '-Cflag=value'])

    _args, kwargs = build_package.call_args
    assert kwargs['isolation'] is False
    assert kwargs['skip_dependency_check'] is True
    assert kwargs['config_settings'] == {'flag': 'value'}
    assert kwargs['installer'] is None


def test_main_sdist_input_end_to_end(tmp_path: pathlib.Path, package_test_setuptools: str) -> None:
    sdist_dir = tmp_path / 'dist'
    sdist_dir.mkdir()
    build.__main__.build_package(package_test_setuptools, str(sdist_dir), ['sdist'])
    archive = next(sdist_dir.glob('*.tar.gz'))

    out_dir = tmp_path / 'out'
    build.__main__.main([str(archive), '--wheel', '-n', '-o', str(out_dir)])

    wheels = list(out_dir.glob('*.whl'))
    assert len(wheels) == 1
    assert wheels[0].name.startswith('test_setuptools-1.0.0')


def test_main_sdist_input_default_outdir_is_archive_parent(
    tmp_path: pathlib.Path,
    sdist: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    build_package = mocker.patch('build.__main__.build_package', return_value=['demo-1.0.0-py3-none-any.whl'])

    build.__main__.main([str(sdist)])

    _, outdir = build_package.call_args.args
    assert outdir == str(tmp_path)


def test_main_non_archive_file_treated_as_directory(tmp_path: pathlib.Path, mocker: pytest_mock.MockerFixture) -> None:
    archive = tmp_path / 'demo-1.0.0.zip'
    archive.write_bytes(b'')
    via_sdist = mocker.patch('build.__main__.build_package_via_sdist', return_value=['something'])

    build.__main__.main([str(archive)])

    via_sdist.assert_called_once()
