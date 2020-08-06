# SPDX-License-Identifier: MIT

import pytest


DUMMY_PYPROJECT = '''
[build-system]
requires = ['flit_core']
build-backend = 'flit_core.buildapi'
'''.strip()


DUMMY_PYPROJECT_NO_BACKEND = '''
[build-system]
requires = []
'''.strip()


DUMMY_PYPROJECT_NO_REQUIRES = '''
[build-system]
build-backend = 'something'
'''.strip()


@pytest.fixture
def empty_file_mock(mocker):
    return mocker.mock_open(read_data='')


@pytest.fixture
def pyproject_mock(mocker):
    return mocker.mock_open(read_data=DUMMY_PYPROJECT)


@pytest.fixture
def pyproject_no_backend_mock(mocker):
    return mocker.mock_open(read_data=DUMMY_PYPROJECT_NO_BACKEND)


@pytest.fixture
def pyproject_no_requires_mock(mocker):
    return mocker.mock_open(read_data=DUMMY_PYPROJECT_NO_REQUIRES)
