# SPDX-License-Identifier: MIT

from __future__ import unicode_literals

import importlib
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
    build_open_owener = 'builtins'
else:  # pragma: no cover
    build_open_owener = 'build'
    FileNotFoundError = IOError
    PermissionError = OSError


DUMMY_METADATA = '''
Version: 1.0.0
Provides-Extra: some_extra
'''.strip()


DUMMY_PYPROJECT = '''
[build-system]
build-backend = 'flit_core.buildapi'
'''.strip()


DUMMY_PYPROJECT_BAD = '''
[build-system]
build-backend = 'missing_backend'
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


def test_init(mocker):
    open_mock = mocker.mock_open(read_data=DUMMY_PYPROJECT)
    modules = {
        'flit_core.buildapi': None,
        'setuptools.build_meta:__legacy__': None,
    }
    mocker.patch('importlib.import_module', modules.get)
    mocker.patch('{}.open'.format(build_open_owener), open_mock)
    mocker.patch('pep517.wrappers.Pep517HookCaller')

    # data = ''
    build.ProjectBuilder('.')
    pep517.wrappers.Pep517HookCaller.assert_called_with('.', 'flit_core.buildapi', backend_path=None)
    pep517.wrappers.Pep517HookCaller.reset_mock()

    # FileNotFoundError
    open_mock.side_effect = FileNotFoundError
    build.ProjectBuilder('.')
    pep517.wrappers.Pep517HookCaller.assert_called_with('.', 'setuptools.build_meta:__legacy__', backend_path=None)

    # PermissionError
    open_mock.side_effect = PermissionError
    with pytest.raises(build.BuildException):
        build.ProjectBuilder('.')
