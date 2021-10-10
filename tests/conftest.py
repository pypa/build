# SPDX-License-Identifier: MIT

import os
import os.path
import platform
import shutil
import stat
import subprocess
import sys
import sysconfig
import tempfile

import pytest

from filelock import FileLock

import build.env


def _build_and_reinstall_build(test_mode):
    temp = tempfile.mkdtemp()
    try:
        subprocess.check_output(
            [sys.executable, '-m', 'build', f'--{test_mode}', '--no-isolation', '--outdir', temp],
        )
        dist_file = next(d for d in os.listdir(temp) if d.endswith('.whl' if test_mode == 'wheel' else '.tar.gz'))
        subprocess.check_call(
            [
                sys.executable,
                '-m',
                'pip',
                'install',
                '--upgrade',  # ``--upgrade`` will uninstall build prior to installing the ``dist_file``
                os.path.join(temp, dist_file),
            ],
        )
    finally:
        shutil.rmtree(temp)


def _one_time_setup():
    test_mode = os.environ.get('TEST_MODE')
    if not test_mode:
        return

    if test_mode == 'path':
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, os.path.join(project_root, 'src'))
    elif test_mode in {'sdist', 'wheel'}:
        status_marker_file = os.path.join(os.environ['TEST_STATUS_DIR'], 'status-marker')
        with FileLock(status_marker_file + '.lock'):
            if not os.path.exists(status_marker_file):
                _build_and_reinstall_build(test_mode)

                with open(status_marker_file, 'wb'):
                    pass


_one_time_setup()


def pytest_addoption(parser):
    os.environ['PYTHONWARNINGS'] = 'ignore:DEPRECATION::pip._internal.cli.base_command'  # for when not run within tox
    os.environ['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'  # do not pollute stderr with upgrade advisory
    parser.addoption('--run-integration', action='store_true', help='run the integration tests')
    parser.addoption('--only-integration', action='store_true', help='only run the integration tests')


PYPY3_WIN_VENV_BAD = platform.python_implementation() == 'PyPy' and os.name == 'nt'
PYPY3_WIN_M = 'https://foss.heptapod.net/pypy/pypy/-/issues/3323 and https://foss.heptapod.net/pypy/pypy/-/issues/3321'


def pytest_collection_modifyitems(config, items):
    skip_int = pytest.mark.skip(reason='integration tests not run (no --run-integration flag)')
    skip_other = pytest.mark.skip(reason='only integration tests are run (got --only-integration flag)')

    if config.getoption('--run-integration') and config.getoption('--only-integration'):  # pragma: no cover
        raise pytest.UsageError("--run-integration and --only-integration can't be used together, choose one")

    if len(items) == 1:  # do not require flags if called directly
        return
    for item in items:
        is_integration_file = is_integration(item)
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
