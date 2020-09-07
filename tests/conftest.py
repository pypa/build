# SPDX-License-Identifier: MIT

import os
import os.path
import shutil
import stat
import sys
import tarfile
import tempfile

import filelock
import pytest

import build


if sys.version_info[0] == 2:
    from urllib2 import urlopen
else:
    from urllib.request import urlopen


INTEGRATION_SOURCES = {
    'dateutil': ('dateutil/dateutil', '2.8.1'),
    'pip': ('pypa/pip', '20.2.1'),
    'Solaar': ('pwr-Solaar/Solaar', '1.0.3'),
    'flit': ('takluyver/flit', '2.3.0'),
}


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


if sys.version_info >= (3, 8):  # pragma: no cover

    def _copy_dir(src, dst, ignore=None):
        shutil.copytree(src, dst, dirs_exist_ok=True, ignore=lambda *_: ignore or [])

else:  # pragma: no cover

    def _copy_dir(src, dst, ignore=None):
        from distutils.dir_util import copy_tree
        for node in os.listdir(src):
            if node in ignore or []:
                continue
            path = os.path.join(src, node)
            root = os.path.join(dst, node)
            if os.path.isdir(path):
                copy_tree(path, root)
            else:
                shutil.copy2(path, root)


@pytest.fixture(scope='session')
def integration_path():
    src_dir = os.path.realpath('.integration-sources')
    dest = tempfile.mkdtemp(prefix='python-build-integration-')

    if not os.path.exists(src_dir):
        os.makedirs(src_dir)

    # for python-build we use our own source directly
    self_source = os.path.abspath(os.path.join(__file__, '..', '..'))
    self_dest = os.path.join(dest, 'python-build')
    if not os.path.exists(self_dest):
        if build.env.fs_supports_symlink():
            os.symlink(self_source, self_dest)
        else:  # pragma: no cover
            _copy_dir(self_source, self_dest, ignore=['.git', '.nox', '.integration-sources'])

    for target, (repo, version) in INTEGRATION_SOURCES.items():
        with filelock.FileLock(os.path.join(src_dir, '{}.lock'.format(target))):
            target_dest = os.path.join(dest, target)
            if os.path.exists(target_dest):  # pragma: no cover
                continue

            tarball = os.path.join(src_dir, '{}.tar.gz'.format(target))
            data = urlopen('https://github.com/{}/archive/{}.tar.gz'.format(repo, version)).read()
            with open(tarball, 'wb') as f:
                f.write(data)

            tarfile.open(tarball, 'r:gz').extractall(dest)
            shutil.move(os.path.join(dest, '{}-{}'.format(repo.split('/')[1], version)), target_dest)

    yield dest

    try:
        os.unlink(self_dest)  # some implementations try to recursively remove the files inside the symlink
        shutil.rmtree(dest)
    except WindowsError:  # pragma: no cover
        '''
        For some reason in some cases we don't have permission to remove
        symlinks on windows, even though we created them?
        '''


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
def test_typo(packages_path):
    return os.path.join(packages_path, 'test-typo')


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
