# SPDX-License-Identifier: MIT

from __future__ import unicode_literals

import copy
import os
import sys

import pep517.wrappers
import pytest

import build


if sys.version_info >= (3, 8):  # pragma: no cover
    from importlib import metadata as importlib_metadata
    import email
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


DUMMY_METADATA = '''
Version: 1.0.0
Provides-Extra: some_extra
'''.strip()


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
    ('requirement_string', 'extra', 'expected'),
    [
        ('something', '', True),
        ('something_else', '', False),
        ('something[extra]', '', False),
        ('something[some_extra]', '', True),
        ('something_else; python_version>"10"', '', True),
        ('something_else; python_version<="1"', '', True),
        ('something_else; python_version>="1"', '', False),
        ('something == 1.0.0', '', True),
        ('something == 2.0.0', '', False),
        ('something[some_extra] == 1.0.0', '', True),
        ('something[some_extra] == 2.0.0', '', False),
    ]
)
def test_check_version(requirement_string, extra, expected):
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
    pep517.wrappers.Pep517HookCaller.assert_called_with(test_flit_path, 'flit_core.buildapi', backend_path=None)
    pep517.wrappers.Pep517HookCaller.reset_mock()

    # FileNotFoundError
    build.ProjectBuilder(legacy_path)
    pep517.wrappers.Pep517HookCaller.assert_called_with(legacy_path, 'setuptools.build_meta:__legacy__', backend_path=None)

    # PermissionError
    if sys.version_info[0] != 2 and os.name != 'nt':  # can't correctly set the permissions required for this
        with pytest.raises(build.BuildException):
            build.ProjectBuilder(test_no_permission)

    # TomlDecodeError
    with pytest.raises(build.BuildException):
        build.ProjectBuilder(test_bad_syntax_path)


def test_check_dependencies(mocker, test_flit_path):
    mocker.patch('importlib.import_module')
    mocker.patch('pep517.wrappers.Pep517HookCaller.get_requires_for_build_sdist')
    mocker.patch('pep517.wrappers.Pep517HookCaller.get_requires_for_build_wheel')
    mocker.patch('build.check_version')

    builder = build.ProjectBuilder(test_flit_path)

    side_effects = [
        [],
        ['something'],
        pep517.wrappers.BackendUnavailable,
    ]

    build.check_version.return_value = False
    builder.hook.get_requires_for_build_sdist.side_effect = copy.copy(side_effects)
    builder.hook.get_requires_for_build_wheel.side_effect = copy.copy(side_effects)

    # requires = []
    assert not builder.check_dependencies('sdist')
    assert not builder.check_dependencies('wheel')

    # requires = ['something']
    assert builder.check_dependencies('sdist')
    assert builder.check_dependencies('wheel')

    # BackendUnavailable
    with pytest.raises(build.BuildBackendException):
        builder.check_dependencies('sdist')
    with pytest.raises(build.BuildBackendException):
        not builder.check_dependencies('wheel')


def test_build(mocker, test_flit_path):
    mocker.patch('importlib.import_module')
    mocker.patch('pep517.wrappers.Pep517HookCaller')

    builder = build.ProjectBuilder(test_flit_path)

    builder.hook.build_sdist.side_effect = [None, Exception]
    builder.hook.build_wheel.side_effect = [None, Exception]

    builder.build('sdist', '.')
    builder.hook.build_sdist.assert_called_with('.', {})

    builder.build('wheel', '.')
    builder.hook.build_wheel.assert_called_with('.', {})

    with pytest.raises(build.BuildBackendException):
        builder.build('sdist', '.')

    with pytest.raises(build.BuildBackendException):
        builder.build('wheel', '.')


def test_default_backend(mocker, legacy_path):
    mocker.patch('importlib.import_module')
    mocker.patch('pep517.wrappers.Pep517HookCaller')

    builder = build.ProjectBuilder(legacy_path)

    assert builder._build_system == build._DEFAULT_BACKEND


def test_missing_backend(mocker, test_no_backend_path):
    mocker.patch('importlib.import_module')
    mocker.patch('pep517.wrappers.Pep517HookCaller')

    builder = build.ProjectBuilder(test_no_backend_path)

    assert builder._build_system == build._DEFAULT_BACKEND


def test_missing_requires(mocker, test_no_requires_path):
    mocker.patch('importlib.import_module')
    mocker.patch('pep517.wrappers.Pep517HookCaller')

    with pytest.raises(build.BuildException):
        build.ProjectBuilder(test_no_requires_path)
