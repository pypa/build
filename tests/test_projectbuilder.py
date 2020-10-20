# SPDX-License-Identifier: MIT

from __future__ import unicode_literals

import copy
import os
import sys
import typing

import pep517.wrappers
import pytest

import build

if sys.version_info >= (3, 8):  # pragma: no cover
    import email
    from importlib import metadata as importlib_metadata

    email_message_from_string = email.message_from_string
else:  # pragma: no cover
    import importlib_metadata

    email_message_from_string = importlib_metadata._compat.email_message_from_string

if sys.version_info >= (3,):  # pragma: no cover
    build_open_owner = 'builtins'
else:  # pragma: no cover
    build_open_owner = 'build'
    FileNotFoundError = IOError
    PermissionError = OSError


DUMMY_METADATA = """
Version: 1.0.0
Provides-Extra: some_extra
""".strip()


DEFAULT_BACKEND = {
    'build-backend': 'setuptools.build_meta:__legacy__',
    'requires': ['setuptools >= 40.8.0', 'wheel'],
}


class MockDistribution(importlib_metadata.Distribution):
    def read_text(self, filename):
        return DUMMY_METADATA

    def locate_file(self, path):  # pragma: no cover
        return ''

    @classmethod
    def from_name(cls, name):
        if name == 'something':
            return cls()
        raise importlib_metadata.PackageNotFoundError


importlib_metadata.Distribution = MockDistribution


@pytest.mark.parametrize(
    ('requirement_string', 'expected', 'extra_warning'),
    [
        ('something', True, False),
        ('something_else', False, False),
        ('something[extra]', False, False),
        ('something[some_extra]', True, True),
        ('something_else; python_version>"10"', True, False),
        ('something_else; python_version<="1"', True, False),
        ('something_else; python_version>="1"', False, False),
        ('something == 1.0.0', True, False),
        ('something == 2.0.0', False, False),
        ('something[some_extra] == 1.0.0', True, True),
        ('something[some_extra] == 2.0.0', False, True),
    ],
)
def test_check_version(requirement_string, expected, extra_warning):
    if extra_warning:
        with pytest.warns(build.IncompleteCheckWarning):
            assert build.check_version(requirement_string) == expected
    else:
        assert build.check_version(requirement_string) == expected


def test_init(mocker, test_flit_path, legacy_path, test_no_permission, test_bad_syntax_path):
    modules = {
        'flit_core.buildapi': None,
        'setuptools.build_meta:__legacy__': None,
    }
    mocker.patch('importlib.import_module', modules.get)
    mocker.patch('pep517.wrappers.Pep517HookCaller')

    # correct flit pyproject.toml
    build.ProjectBuilder(test_flit_path)
    pep517.wrappers.Pep517HookCaller.assert_called_with(
        test_flit_path,
        'flit_core.buildapi',
        backend_path=None,
        python_executable=sys.executable,
    )
    pep517.wrappers.Pep517HookCaller.reset_mock()

    # custom python
    build.ProjectBuilder(test_flit_path, python_executable='some-python')
    pep517.wrappers.Pep517HookCaller.assert_called_with(
        test_flit_path,
        'flit_core.buildapi',
        backend_path=None,
        python_executable='some-python',
    )
    pep517.wrappers.Pep517HookCaller.reset_mock()

    # FileNotFoundError
    build.ProjectBuilder(legacy_path)
    pep517.wrappers.Pep517HookCaller.assert_called_with(
        legacy_path,
        'setuptools.build_meta:__legacy__',
        backend_path=None,
        python_executable=sys.executable,
    )

    # PermissionError
    if sys.version_info[0] != 2 and os.name != 'nt':  # can't correctly set the permissions required for this
        with pytest.raises(build.BuildException):
            build.ProjectBuilder(test_no_permission)

    # TomlDecodeError
    with pytest.raises(build.BuildException):
        build.ProjectBuilder(test_bad_syntax_path)


@pytest.mark.parametrize('value', [b'something', typing.Text('something_else')])
def test_python_executable(test_flit_path, value):
    builder = build.ProjectBuilder(test_flit_path)

    builder.python_executable = value
    assert builder.python_executable == value
    assert builder._hook.python_executable == value


@pytest.mark.parametrize('distribution', ['wheel', 'sdist'])
def test_get_dependencies_missing_backend(packages_path, distribution):
    bad_backend_path = os.path.join(packages_path, 'test-bad-backend')
    builder = build.ProjectBuilder(bad_backend_path)

    with pytest.raises(build.BuildException):
        builder.get_dependencies(distribution)


@pytest.mark.parametrize('distribution', ['wheel', 'sdist'])
def test_build_missing_backend(packages_path, distribution, tmpdir):
    bad_backend_path = os.path.join(packages_path, 'test-bad-backend')
    builder = build.ProjectBuilder(bad_backend_path)

    with pytest.raises(build.BuildException):
        builder.build(distribution, str(tmpdir))


def test_check_dependencies(mocker, test_flit_path):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('pep517.wrappers.Pep517HookCaller.get_requires_for_build_sdist')
    mocker.patch('pep517.wrappers.Pep517HookCaller.get_requires_for_build_wheel')
    mocker.patch('build.check_version', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)

    side_effects = [
        [],
        ['something'],
        pep517.wrappers.BackendUnavailable,
    ]

    build.check_version.return_value = False
    builder._hook.get_requires_for_build_sdist.side_effect = copy.copy(side_effects)
    builder._hook.get_requires_for_build_wheel.side_effect = copy.copy(side_effects)

    # requires = []
    assert builder.check_dependencies('sdist') == {'flit_core >=2,<3'}
    assert builder.check_dependencies('wheel') == {'flit_core >=2,<3'}

    # requires = ['something']
    assert builder.check_dependencies('sdist') == {'flit_core >=2,<3', 'something'}
    assert builder.check_dependencies('wheel') == {'flit_core >=2,<3', 'something'}

    # BackendUnavailable
    with pytest.raises(build.BuildBackendException):
        builder.check_dependencies('sdist')
    with pytest.raises(build.BuildBackendException):
        not builder.check_dependencies('wheel')


def test_working_directory(tmp_dir):
    assert os.path.realpath(os.curdir) != os.path.realpath(tmp_dir)
    with build._working_directory(tmp_dir):
        assert os.path.realpath(os.curdir) == os.path.realpath(tmp_dir)


def test_build(mocker, test_flit_path, tmp_dir):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)
    mocker.patch('build._working_directory', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)

    builder._hook.build_sdist.side_effect = [None, Exception]
    builder._hook.build_wheel.side_effect = [None, Exception]

    builder.build('sdist', tmp_dir)
    builder._hook.build_sdist.assert_called_with(tmp_dir, {})
    build._working_directory.assert_called_with(test_flit_path)

    builder.build('wheel', tmp_dir)
    builder._hook.build_wheel.assert_called_with(tmp_dir, {})
    build._working_directory.assert_called_with(test_flit_path)

    with pytest.raises(build.BuildBackendException):
        build._working_directory.assert_called_with(test_flit_path)
        builder.build('sdist', tmp_dir)

    with pytest.raises(build.BuildBackendException):
        build._working_directory.assert_called_with(test_flit_path)
        builder.build('wheel', tmp_dir)


def test_default_backend(mocker, legacy_path):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(legacy_path)

    assert builder._build_system == DEFAULT_BACKEND


def test_missing_backend(mocker, test_no_backend_path):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_no_backend_path)

    assert builder._build_system == DEFAULT_BACKEND


def test_missing_requires(mocker, test_no_requires_path):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    with pytest.raises(build.BuildException):
        build.ProjectBuilder(test_no_requires_path)


def test_build_system_typo(mocker, test_typo):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    with pytest.warns(build.TypoWarning):
        build.ProjectBuilder(test_typo)


def test_missing_outdir(mocker, tmp_dir, test_flit_path):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)
    out = os.path.join(tmp_dir, 'out')

    builder.build('sdist', out)

    assert os.path.isdir(out)


def test_relative_outdir(mocker, tmp_dir, test_flit_path):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)

    builder.build('sdist', '.')

    builder._hook.build_sdist.assert_called_with(os.path.abspath('.'), {})


def test_not_dir_outdir(mocker, tmp_dir, test_flit_path):
    mocker.patch('importlib.import_module', autospec=True)
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)
    out = os.path.join(tmp_dir, 'out')

    open(out, 'a').close()  # create empty file

    with pytest.raises(build.BuildException):
        builder.build('sdist', out)
