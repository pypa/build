# SPDX-License-Identifier: MIT

import contextlib
import os
import os.path
import shutil
import stat
import sys
import sysconfig
import tempfile

import pytest

import build.env


if sys.version_info < (3, 8):
    import importlib_metadata as metadata
else:
    from importlib import metadata


def pytest_addoption(parser):
    os.environ['PYTHONWARNINGS'] = 'ignore:DEPRECATION::pip._internal.cli.base_command'  # for when not run within tox
    os.environ['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'  # do not pollute stderr with upgrade advisory
    parser.addoption('--run-integration', action='store_true', help='run the integration tests')
    parser.addoption('--only-integration', action='store_true', help='only run the integration tests')


PYPY3_WIN_VENV_BAD = (
    sys.implementation.name == 'pypy' and sys.implementation.version < (7, 3, 9) and sys.platform.startswith('win')
)
PYPY3_WIN_M = 'https://foss.heptapod.net/pypy/pypy/-/issues/3323 and https://foss.heptapod.net/pypy/pypy/-/issues/3321'


def pytest_collection_modifyitems(config, items):
    skip_int = pytest.mark.skip(reason='integration tests not run (no --run-integration flag)')
    skip_other = pytest.mark.skip(reason='only integration tests are run (got --only-integration flag)')

    if config.getoption('--run-integration') and config.getoption('--only-integration'):  # pragma: no cover
        msg = "--run-integration and --only-integration can't be used together, choose one"
        raise pytest.UsageError(msg)

    if len(items) == 1:  # do not require flags if called directly
        return
    for item in items:
        is_integration_file = is_integration(item)
        if PYPY3_WIN_VENV_BAD and item.get_closest_marker('pypy3323bug') and os.environ.get('PYPY3323BUG', None):
            item.add_marker(pytest.mark.xfail(reason=PYPY3_WIN_M, strict=False))
        if PYPY3_WIN_VENV_BAD and item.get_closest_marker('isolated'):
            if not (is_integration_file and item.originalname == 'test_build') or (
                hasattr(item, 'callspec') and '--no-isolation' not in item.callspec.params.get('args', [])
            ):
                item.add_marker(pytest.mark.xfail(reason=PYPY3_WIN_M, strict=True))
        if is_integration_file:  # pragma: no cover
            if not config.getoption('--run-integration') and not config.getoption('--only-integration'):
                item.add_marker(skip_int)
        elif config.getoption('--only-integration'):  # pragma: no cover
            item.add_marker(skip_other)
    # run integration tests after unit tests
    items.sort(key=lambda i: 1 if is_integration(i) else 0)


def is_integration(item):
    return os.path.basename(item.location[0]) == 'test_integration.py'


@pytest.fixture()
def local_pip(monkeypatch):
    monkeypatch.setattr(build.env, '_valid_global_pip', lambda: None)


@pytest.fixture(scope='session', autouse=True)
def ensure_syconfig_vars_created():
    # the config vars are globally cached and may use get_path, make sure they are created
    sysconfig.get_config_vars()


@pytest.fixture
def packages_path():
    return os.path.realpath(os.path.join(__file__, '..', 'packages'))


def generate_package_path_fixture(package_name):
    @pytest.fixture
    def fixture(packages_path):
        return os.path.join(packages_path, package_name)

    return fixture


# Generate path fixtures dynamically.
package_names = os.listdir(os.path.join(os.path.dirname(__file__), 'packages'))
for package_name in package_names:
    normalized_name = package_name.replace('-', '_')
    fixture_name = f'package_{normalized_name}'
    globals()[fixture_name] = generate_package_path_fixture(package_name)


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


@pytest.fixture(autouse=True)
def force_venv(mocker):
    mocker.patch.object(build.env, '_should_use_virtualenv', lambda: False)


def pytest_report_header() -> str:
    interesting_packages = [
        'build',
        'colorama',
        'filelock',
        'packaging',
        'pip',
        'pyproject_hooks',
        'setuptools',
        'tomli',
        'virtualenv',
        'wheel',
    ]
    valid = []
    for package in interesting_packages:
        # Old versions of importlib_metadata made this FileNotFoundError
        with contextlib.suppress(ModuleNotFoundError, FileNotFoundError):
            valid.append(f'{package}=={metadata.version(package)}')
    reqs = ' '.join(valid)
    return f'installed packages of interest: {reqs}'
