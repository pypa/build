# SPDX-License-Identifier: MIT

import os
import os.path
import shutil
import stat
import tempfile

import pytest


def pytest_addoption(parser):
    parser.addoption('--run-integration', action='store_true', help='run the integration tests')
    parser.addoption('--only-integration', action='store_true', help='only run the integration tests')


def pytest_collection_modifyitems(config, items):
    skip_int = pytest.mark.skip(reason='integration tests not run')
    skip_other = pytest.mark.skip(reason='only integration tests are run')

    if config.getoption('--run-integration') and config.getoption('--only-integration'):  # pragma: no cover
        raise pytest.UsageError("--run-integration and --only-integration can't be used together, choose one")

    for item in items:
        if os.path.basename(item.location[0]) == 'test_integration.py':  # pragma: no cover
            if not config.getoption('--run-integration') and not config.getoption('--only-integration'):
                item.add_marker(skip_int)
        elif config.getoption('--only-integration'):  # pragma: no cover
            item.add_marker(skip_other)


@pytest.fixture
def packages_path():
    return os.path.realpath(os.path.join(__file__, '..', 'packages'))


@pytest.fixture
def integration_path():
    return os.path.realpath(os.path.join(__file__, '..', 'integration'))


@pytest.fixture
def legacy_path(packages_path):
    return os.path.join(packages_path, 'legacy')


@pytest.fixture
def test_flit_path(packages_path):
    return os.path.join(packages_path, 'test-flit')


@pytest.fixture
def test_bad_syntax_path(packages_path):
    return os.path.join(packages_path, 'test-bad-syntax')


@pytest.fixture
def test_no_backend_path(packages_path):
    return os.path.join(packages_path, 'test-no-backend')


@pytest.fixture
def test_no_requires_path(packages_path):
    return os.path.join(packages_path, 'test-no-requires')


@pytest.fixture
def test_no_permission(packages_path):
    path = os.path.join(packages_path, 'test-no-permission')
    file = os.path.join(path, 'pyproject.toml')
    orig_stat = os.stat(file).st_mode

    os.chmod(file, ~stat.S_IRWXU)

    yield os.path.join(packages_path, 'test-no-permission')

    os.chmod(file, orig_stat)


@pytest.fixture
def tmp_dir():
    path = tempfile.mkdtemp(prefix='python-build-test-')

    yield path

    shutil.rmtree(path)
