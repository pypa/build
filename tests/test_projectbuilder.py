# SPDX-License-Identifier: MIT

from __future__ import unicode_literals

import sys

import pytest

import build


if sys.version_info >= (3, 8):  # pragma: no cover
    from importlib import metadata as importlib_metadata
    import email
    email_message_from_string = email.message_from_string
else:  # pragma: no cover
    import importlib_metadata
    email_message_from_string = importlib_metadata._compat.email_message_from_string


DUMMY_METADATA = '''
Version: 1.0.0
Provides-Extra: some_extra
'''.strip()


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

    assert build.check_version(requirement_string) == expected
