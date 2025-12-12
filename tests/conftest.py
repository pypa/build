# SPDX-License-Identifier: MIT

from __future__ import annotations

import contextlib
import contextvars
import importlib.metadata
import os
import os.path
import shutil
import stat
import sys
import sysconfig
import tempfile

from functools import partial, update_wrapper
from pathlib import Path

import pytest

import build.env

from build._compat import tomllib


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


def pytest_runtest_call(item: pytest.Item):
    if item.get_closest_marker('contextvars'):
        if isinstance(item, pytest.Function):
            wrapped_function = partial(contextvars.copy_context().run, item.obj)
            item.obj = update_wrapper(wrapped_function, item.obj)
        else:
            msg = 'cannot rewrap non-function item'
            raise RuntimeError(msg)


@pytest.fixture
def local_pip(monkeypatch):
    monkeypatch.setattr(build.env._PipBackend, '_has_valid_outer_pip', None)


@pytest.fixture(autouse=True)
def avoid_constraints(monkeypatch):
    monkeypatch.delenv('PIP_CONSTRAINT', raising=False)
    monkeypatch.delenv('UV_CONSTRAINT', raising=False)


@pytest.fixture(autouse=True, params=[False])
def has_virtualenv(request, monkeypatch):
    if request.param is not None:
        monkeypatch.setattr(build.env._PipBackend, '_has_virtualenv', request.param)


@pytest.fixture(scope='session', autouse=True)
def ensure_syconfig_vars_created():
    # the config vars are globally cached and may use get_path, make sure they are created
    sysconfig.get_config_vars()


@pytest.fixture
def packages_path():
    return os.path.realpath(os.path.join(__file__, '..', 'packages'))


def is_setuptools(package_path):
    if package_path.joinpath('setup.py').is_file():
        return True
    pyproject = package_path / 'pyproject.toml'
    try:
        with pyproject.open('rb') as f:
            pp = tomllib.load(f)
    except (FileNotFoundError, ValueError):
        return True
    return 'setuptools' in pp.get('build-system', {}).get('build-backend', 'setuptools')


def generate_package_path_fixture(package_name):
    @pytest.fixture
    def fixture(packages_path, tmp_path):
        package_path = Path(packages_path) / package_name
        if not is_setuptools(package_path):
            return str(package_path)

        new_path = tmp_path / package_name
        shutil.copytree(package_path, new_path)
        return str(new_path)

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


def pytest_report_header() -> str:
    interesting_packages = [
        'build',
        'colorama',
        'coverage',
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
            valid.append(f'{package}=={importlib.metadata.version(package)}')
    reqs = ' '.join(valid)
    return f'installed packages of interest: {reqs}'


@pytest.fixture
def subtests(request: pytest.FixtureRequest):
    try:
        return request.getfixturevalue('subtests')
    except pytest.FixtureLookupError:

        class Subtests:
            @contextlib.contextmanager
            def test(msg: str | None = None, **kwargs: object):
                yield

        return Subtests()
