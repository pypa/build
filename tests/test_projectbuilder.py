# SPDX-License-Identifier: MIT

from __future__ import annotations

import copy
import logging
import os
import pathlib
import sys
import textwrap

from typing import NoReturn

import pyproject_hooks
import pytest

import build
import build._builder

from build._compat import importlib as _importlib


build_open_owner = 'builtins'


DEFAULT_BACKEND = {
    'build-backend': 'setuptools.build_meta:__legacy__',
    'requires': ['setuptools >= 40.8.0'],
}


class MockDistribution(_importlib.metadata.Distribution):
    def locate_file(self, path):  # pragma: no cover
        return ''

    @classmethod
    def from_name(cls, name):
        if name == 'extras_dep':
            return ExtraMockDistribution()
        elif name == 'requireless_dep':
            return RequirelessMockDistribution()
        elif name == 'recursive_dep':
            return RecursiveMockDistribution()
        elif name == 'prerelease_dep':
            return PrereleaseMockDistribution()
        elif name == 'circular_dep':
            return CircularMockDistribution()
        elif name == 'nested_circular_dep':
            return NestedCircularMockDistribution()
        raise _importlib.metadata.PackageNotFoundError


class ExtraMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return textwrap.dedent(
                """
                Metadata-Version: 2.2
                Name: extras_dep
                Version: 1.0.0
                Provides-Extra: extra-without-associated-deps
                Provides-Extra: extra-with_unmet-deps
                Requires-Dist: unmet_dep; extra == 'extra-with-unmet-deps'
                Provides-Extra: extra-with-met-deps
                Requires-Dist: extras_dep; extra == 'extra-with-met-deps'
                Provides-Extra: recursive-extra-with-unmet-deps
                Requires-Dist: recursive_dep; extra == 'recursive-extra-with-unmet-deps'
                """
            ).strip()


class RequirelessMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return textwrap.dedent(
                """
                Metadata-Version: 2.2
                Name: requireless_dep
                Version: 1.0.0
                """
            ).strip()


class RecursiveMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return textwrap.dedent(
                """
                Metadata-Version: 2.2
                Name: recursive_dep
                Version: 1.0.0
                Requires-Dist: recursive_unmet_dep
                """
            ).strip()


class PrereleaseMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return textwrap.dedent(
                """
                Metadata-Version: 2.2
                Name: prerelease_dep
                Version: 1.0.1a0
                """
            ).strip()


class CircularMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return textwrap.dedent(
                """
                Metadata-Version: 2.2
                Name: circular_dep
                Version: 1.0.0
                Requires-Dist: nested_circular_dep
                """
            ).strip()


class NestedCircularMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return textwrap.dedent(
                """
                Metadata-Version: 2.2
                Name: nested_circular_dep
                Version: 1.0.0
                Requires-Dist: circular_dep
                """
            ).strip()


@pytest.mark.parametrize(
    ('requirement_string', 'expected'),
    [
        ('extras_dep', None),
        ('missing_dep', ('missing_dep',)),
        ('requireless_dep', None),
        ('extras_dep[undefined_extra]', None),
        # would the wheel builder filter this out?
        ('extras_dep[extra-without-associated-deps]', None),
        (
            'extras_dep[extra-with-unmet-deps]',
            ('extras_dep[extra-with-unmet-deps]', 'unmet_dep; extra == "extra-with-unmet-deps"'),
        ),
        (
            'extras_dep[recursive-extra-with-unmet-deps]',
            (
                'extras_dep[recursive-extra-with-unmet-deps]',
                'recursive_dep; extra == "recursive-extra-with-unmet-deps"',
                'recursive_unmet_dep',
            ),
        ),
        ('extras_dep[extra-with-met-deps]', None),
        ('missing_dep; python_version>"10"', None),
        ('missing_dep; python_version<="1"', None),
        ('missing_dep; python_version>="1"', ('missing_dep; python_version >= "1"',)),
        ('extras_dep == 1.0.0', None),
        ('extras_dep == 2.0.0', ('extras_dep==2.0.0',)),
        ('extras_dep[extra-without-associated-deps] == 1.0.0', None),
        ('extras_dep[extra-without-associated-deps] == 2.0.0', ('extras_dep[extra-without-associated-deps]==2.0.0',)),
        ('prerelease_dep >= 1.0.0', None),
        ('circular_dep', None),
    ],
)
def test_check_dependency(monkeypatch, requirement_string, expected):
    monkeypatch.setattr(_importlib.metadata, 'Distribution', MockDistribution)
    assert next(build.check_dependency(requirement_string), None) == expected


def test_bad_project(package_test_no_project):
    # Passing a nonexistent project directory
    with pytest.raises(build.BuildException):
        build.ProjectBuilder(os.path.join(package_test_no_project, 'does-not-exist'))
    # Passing a file as a project directory
    with pytest.raises(build.BuildException):
        build.ProjectBuilder(os.path.join(package_test_no_project, 'empty.txt'))
    # Passing a project directory with no pyproject.toml or setup.py
    with pytest.raises(build.BuildException):
        build.ProjectBuilder(package_test_no_project)


def test_init(mocker, package_test_flit, package_legacy, test_no_permission, package_test_bad_syntax):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller')

    # correct flit pyproject.toml
    builder = build.ProjectBuilder(package_test_flit)
    pyproject_hooks.BuildBackendHookCaller.assert_called_with(
        package_test_flit, 'flit_core.buildapi', backend_path=None, python_executable=sys.executable, runner=builder._runner
    )
    pyproject_hooks.BuildBackendHookCaller.reset_mock()

    # custom python
    builder = build.ProjectBuilder(package_test_flit, python_executable='some-python')
    pyproject_hooks.BuildBackendHookCaller.assert_called_with(
        package_test_flit, 'flit_core.buildapi', backend_path=None, python_executable='some-python', runner=builder._runner
    )
    pyproject_hooks.BuildBackendHookCaller.reset_mock()

    # FileNotFoundError
    builder = build.ProjectBuilder(package_legacy)
    pyproject_hooks.BuildBackendHookCaller.assert_called_with(
        package_legacy,
        'setuptools.build_meta:__legacy__',
        backend_path=None,
        python_executable=sys.executable,
        runner=builder._runner,
    )

    # PermissionError
    if not sys.platform.startswith('win'):  # can't correctly set the permissions required for this
        with pytest.raises(build.BuildException):
            build.ProjectBuilder(test_no_permission)

    # TomlDecodeError
    with pytest.raises(build.BuildException):
        build.ProjectBuilder(package_test_bad_syntax)


def test_init_makes_source_dir_absolute(package_test_flit):
    rel_dir = os.path.relpath(package_test_flit, os.getcwd())
    assert not os.path.isabs(rel_dir)
    builder = build.ProjectBuilder(rel_dir)
    assert os.path.isabs(builder.source_dir)


@pytest.mark.parametrize('distribution', ['wheel', 'sdist'])
def test_get_requires_for_build_missing_backend(packages_path, distribution):
    bad_backend_path = os.path.join(packages_path, 'test-bad-backend')
    builder = build.ProjectBuilder(bad_backend_path)

    with pytest.raises(build.BuildBackendException):
        builder.get_requires_for_build(distribution)


@pytest.mark.parametrize('distribution', ['wheel', 'sdist'])
def test_get_requires_for_build_missing_optional_hooks(package_test_optional_hooks, distribution):
    builder = build.ProjectBuilder(package_test_optional_hooks)

    assert builder.get_requires_for_build(distribution) == set()


@pytest.mark.parametrize('distribution', ['wheel', 'sdist'])
def test_build_missing_backend(packages_path, distribution, tmpdir):
    bad_backend_path = os.path.join(packages_path, 'test-bad-backend')
    builder = build.ProjectBuilder(bad_backend_path)

    with pytest.raises(build.BuildBackendException):
        builder.build(distribution, str(tmpdir))


def _nothing_installed(name: str) -> NoReturn:
    raise _importlib.metadata.PackageNotFoundError(name)


def test_check_dependencies(mocker, package_test_flit, monkeypatch):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller.get_requires_for_build_sdist')
    mocker.patch('pyproject_hooks.BuildBackendHookCaller.get_requires_for_build_wheel')

    monkeypatch.setattr(_importlib.metadata, 'distribution', _nothing_installed)

    builder = build.ProjectBuilder(package_test_flit)

    side_effects = [
        [],
        ['something'],
        pyproject_hooks.BackendUnavailable,
    ]

    builder._hook.get_requires_for_build_sdist.side_effect = copy.copy(side_effects)
    builder._hook.get_requires_for_build_wheel.side_effect = copy.copy(side_effects)

    # requires = []
    assert builder.check_dependencies('sdist') == {('flit_core<4,>=2',)}
    assert builder.check_dependencies('wheel') == {('flit_core<4,>=2',)}

    # requires = ['something']
    assert builder.check_dependencies('sdist') == {('flit_core<4,>=2',), ('something',)}
    assert builder.check_dependencies('wheel') == {('flit_core<4,>=2',), ('something',)}

    # BackendUnavailable
    with pytest.raises(build.BuildBackendException):
        builder.check_dependencies('sdist')
    with pytest.raises(build.BuildBackendException):
        not builder.check_dependencies('wheel')


def test_build(mocker, package_test_flit, tmp_dir):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_test_flit)

    builder._hook.build_sdist.side_effect = ['dist.tar.gz', Exception]
    builder._hook.build_wheel.side_effect = ['dist.whl', Exception]

    assert builder.build('sdist', tmp_dir) == os.path.join(tmp_dir, 'dist.tar.gz')
    builder._hook.build_sdist.assert_called_with(tmp_dir, None)

    assert builder.build('wheel', tmp_dir) == os.path.join(tmp_dir, 'dist.whl')
    builder._hook.build_wheel.assert_called_with(tmp_dir, None)

    with pytest.raises(build.BuildBackendException):
        builder.build('sdist', tmp_dir)

    with pytest.raises(build.BuildBackendException):
        builder.build('wheel', tmp_dir)


def test_default_backend(mocker, package_legacy):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_legacy)

    assert builder._build_system == DEFAULT_BACKEND


def test_missing_backend(mocker, package_test_no_backend):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_test_no_backend)

    assert builder._build_system == {'requires': [], 'build-backend': DEFAULT_BACKEND['build-backend']}


def test_missing_requires(mocker, package_test_no_requires):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    with pytest.raises(build.BuildException):
        build.ProjectBuilder(package_test_no_requires)


def test_build_system_typo(mocker, package_test_typo):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    with pytest.warns(build.TypoWarning):
        build.ProjectBuilder(package_test_typo)


def test_missing_outdir(mocker, tmp_dir, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_test_flit)
    builder._hook.build_sdist.return_value = 'dist.tar.gz'
    out = os.path.join(tmp_dir, 'out')

    builder.build('sdist', out)

    assert os.path.isdir(out)


def test_relative_outdir(mocker, tmp_dir, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_test_flit)
    builder._hook.build_sdist.return_value = 'dist.tar.gz'

    builder.build('sdist', '.')

    builder._hook.build_sdist.assert_called_with(os.path.abspath('.'), None)


def test_build_not_dir_outdir(mocker, tmp_dir, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_test_flit)
    builder._hook.build_sdist.return_value = 'dist.tar.gz'
    out = os.path.join(tmp_dir, 'out')

    open(out, 'a', encoding='utf-8').close()  # create empty file

    with pytest.raises(build.BuildException):
        builder.build('sdist', out)


@pytest.fixture(scope='session')
def demo_pkg_inline(tmp_path_factory):
    # builds a wheel without any dependencies and with a console script demo-pkg-inline
    tmp_path = tmp_path_factory.mktemp('demo-pkg-inline')
    builder = build.ProjectBuilder(source_dir=os.path.join(os.path.dirname(__file__), 'packages', 'inline'))
    out = tmp_path / 'dist'
    builder.build('wheel', str(out))
    return next(out.iterdir())


@pytest.mark.contextvars
@pytest.mark.isolated
def test_build_with_dep_on_console_script(tmp_path, demo_pkg_inline, capfd, mocker):
    """
    All command-line scripts provided by the build-required packages must be present in the build environment's PATH.
    """
    # we first install demo pkg inline as build dependency (as this provides a console script we can check)
    # to validate backend invocations contain the correct path we use an inline backend that will fail, but first
    # provides the PATH information (and validates shutil.which is able to discover the executable - as PEP states)
    toml = textwrap.dedent(
        """
        [build-system]
        requires = ["demo_pkg_inline"]
        build-backend = "build"
        backend-path = ["."]

        [project]
        description = "Factory ⸻ A code generator 🏭"
        authors = [{name = "Łukasz Langa"}]
        """
    )
    code = textwrap.dedent(
        """
        import os
        import shutil
        import sys
        print("BB " + os.environ["PATH"])
        exe_at = shutil.which("demo-pkg-inline")
        print("BB " + exe_at)
        """
    )
    (tmp_path / 'pyproject.toml').write_text(toml, encoding='UTF-8')
    (tmp_path / 'build.py').write_text(code, encoding='utf-8')

    deps = {str(demo_pkg_inline)}  # we patch the requires demo_pkg_inline to refer to the wheel -> we don't need index
    mocker.patch('build.ProjectBuilder.build_system_requires', new_callable=mocker.PropertyMock, return_value=deps)
    from build.__main__ import main

    with pytest.raises(SystemExit):
        main(['--wheel', '--outdir', str(tmp_path / 'dist'), str(tmp_path)])

    out, _ = capfd.readouterr()
    lines = [line[3:] for line in out.splitlines() if line.startswith('BB ')]  # filter for our markers
    path_vars = lines[0].split(os.pathsep)
    which_detected = lines[1]
    assert which_detected.startswith(path_vars[0]), out


def test_prepare(mocker, tmp_dir, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_test_flit)
    builder._hook.prepare_metadata_for_build_wheel.return_value = 'dist-1.0.dist-info'

    assert builder.prepare('wheel', tmp_dir) == os.path.join(tmp_dir, 'dist-1.0.dist-info')
    builder._hook.prepare_metadata_for_build_wheel.assert_called_with(tmp_dir, None, _allow_fallback=False)


def test_prepare_no_hook(mocker, tmp_dir, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_test_flit)
    failure = pyproject_hooks.HookMissing('prepare_metadata_for_build_wheel')
    builder._hook.prepare_metadata_for_build_wheel.side_effect = failure

    assert builder.prepare('wheel', tmp_dir) is None


def test_prepare_error(mocker, tmp_dir, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_test_flit)
    builder._hook.prepare_metadata_for_build_wheel.side_effect = Exception

    with pytest.raises(build.BuildBackendException, match='Backend operation failed: Exception'):
        builder.prepare('wheel', tmp_dir)


def test_prepare_not_dir_outdir(mocker, tmp_dir, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)

    builder = build.ProjectBuilder(package_test_flit)

    out = os.path.join(tmp_dir, 'out')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('Not a directory')
    with pytest.raises(build.BuildException, match=r'Build path .* exists and is not a directory'):
        builder.prepare('wheel', out)


def test_no_outdir_single(mocker, tmp_dir, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller.prepare_metadata_for_build_wheel', return_value='')

    builder = build.ProjectBuilder(package_test_flit)

    out = os.path.join(tmp_dir, 'out')
    builder.prepare('wheel', out)

    assert os.path.isdir(out)


def test_no_outdir_multiple(mocker, tmp_dir, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller.prepare_metadata_for_build_wheel', return_value='')

    builder = build.ProjectBuilder(package_test_flit)

    out = os.path.join(tmp_dir, 'does', 'not', 'exist')
    builder.prepare('wheel', out)

    assert os.path.isdir(out)


def test_runner_user_specified(tmp_dir, package_test_flit):
    def dummy_runner(cmd, cwd=None, extra_environ=None):
        msg = 'Runner was called'
        raise RuntimeError(msg)

    builder = build.ProjectBuilder(package_test_flit, runner=dummy_runner)
    with pytest.raises(build.BuildBackendException, match='Runner was called'):
        builder.build('wheel', tmp_dir)


def test_metadata_path_no_prepare(tmp_dir, package_test_no_prepare):
    builder = build.ProjectBuilder(package_test_no_prepare)

    metadata = _importlib.metadata.PathDistribution(
        pathlib.Path(builder.metadata_path(tmp_dir)),
    ).metadata

    assert metadata['name'] == 'test-no-prepare'
    assert metadata['Version'] == '1.0.0'


def test_metadata_path_with_prepare(tmp_dir, package_test_setuptools):
    builder = build.ProjectBuilder(package_test_setuptools)

    metadata = _importlib.metadata.PathDistribution(
        pathlib.Path(builder.metadata_path(tmp_dir)),
    ).metadata

    # Setuptools < v69.0.3 (https://github.com/pypa/setuptools/pull/4159) normalized this to dashes
    assert metadata['name'].replace('-', '_') == 'test_setuptools'
    assert metadata['Version'] == '1.0.0'


def test_metadata_path_legacy(tmp_dir, package_legacy):
    builder = build.ProjectBuilder(package_legacy)

    metadata = _importlib.metadata.PathDistribution(
        pathlib.Path(builder.metadata_path(tmp_dir)),
    ).metadata

    assert metadata['name'] == 'legacy'
    assert metadata['Version'] == '1.0.0'


def test_metadata_invalid_wheel(tmp_dir, package_test_bad_wheel):
    builder = build.ProjectBuilder(package_test_bad_wheel)

    with pytest.raises(ValueError, match='Invalid wheel'):
        builder.metadata_path(tmp_dir)


def test_log(mocker, caplog, package_test_flit):
    mocker.patch('pyproject_hooks.BuildBackendHookCaller', autospec=True)
    mocker.patch('build.ProjectBuilder._call_backend', return_value='some_path')
    caplog.set_level(logging.DEBUG)

    builder = build.ProjectBuilder(package_test_flit)
    builder.get_requires_for_build('sdist')
    builder.get_requires_for_build('wheel')
    builder.prepare('wheel', '.')
    builder.build('sdist', '.')
    builder.build('wheel', '.')

    assert [(record.levelname, record.message) for record in caplog.records] == [
        ('INFO', 'Getting build dependencies for sdist...'),
        ('INFO', 'Getting build dependencies for wheel...'),
        ('INFO', 'Getting metadata for wheel...'),
        ('INFO', 'Building sdist...'),
        ('INFO', 'Building wheel...'),
    ]


@pytest.mark.parametrize(
    ('pyproject_toml', 'parse_output'),
    [
        (
            {'build-system': {'requires': ['foo']}},
            {'requires': ['foo'], 'build-backend': 'setuptools.build_meta:__legacy__'},
        ),
        (
            {'build-system': {'requires': ['foo'], 'build-backend': 'bar'}},
            {'requires': ['foo'], 'build-backend': 'bar'},
        ),
        (
            {'build-system': {'requires': ['foo'], 'build-backend': 'bar', 'backend-path': ['baz']}},
            {'requires': ['foo'], 'build-backend': 'bar', 'backend-path': ['baz']},
        ),
    ],
)
def test_parse_valid_build_system_table_type(pyproject_toml, parse_output):
    assert build._builder._parse_build_system_table(pyproject_toml) == parse_output


@pytest.mark.parametrize(
    ('pyproject_toml', 'error_message'),
    [
        (
            {'build-system': {}},
            '`requires` is a required property',
        ),
        (
            {'build-system': {'requires': 'not an array'}},
            '`requires` must be an array of strings',
        ),
        (
            {'build-system': {'requires': [1]}},
            '`requires` must be an array of strings',
        ),
        (
            {'build-system': {'requires': ['foo'], 'build-backend': ['not a string']}},
            '`build-backend` must be a string',
        ),
        (
            {'build-system': {'requires': ['foo'], 'backend-path': 'not an array'}},
            '`backend-path` must be an array of strings',
        ),
        (
            {'build-system': {'requires': ['foo'], 'backend-path': [1]}},
            '`backend-path` must be an array of strings',
        ),
        (
            {'build-system': {'requires': ['foo'], 'unknown-prop': False}},
            'Unknown properties: unknown-prop',
        ),
    ],
)
def test_parse_invalid_build_system_table_type(pyproject_toml, error_message):
    with pytest.raises(build.BuildSystemTableValidationError, match=error_message):
        build._builder._parse_build_system_table(pyproject_toml)
