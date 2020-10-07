# SPDX-License-Identifier: MIT

import os
import os.path
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import subprocess

import filelock
import pytest

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


def _setup():
    """At the start of the test suite initialize the environment in case of path/wheel/sdist mode"""
    mode = os.environ.get("TEST_MODE")
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
    if mode == "path":
        sys.path.insert(0, root)
    elif mode in ("wheel", "sdist"):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root)
        temp = tempfile.mkdtemp()
        try:
            cmd = [sys.executable, "-m", "build", "--{}".format(mode), "--no-isolation", "--outdir", str(temp)]
            subprocess.check_output(cmd, env=env)
            pkg = next(t for t in os.listdir(temp) if (t.endswith(".whl" if mode == "wheel" else ".tar.gz")))
            subprocess.check_call([sys.executable, "-m", "pip", "install", os.path.join(temp, pkg)])
        finally:
            shutil.rmtree(temp)


_setup()


def pytest_addoption(parser):
    parser.addoption('--run-integration', action='store_true', help='run the integration tests')
    parser.addoption('--only-integration', action='store_true', help='only run the integration tests')


PYPY3_WIN_VENV_BAD = platform.python_implementation() == 'PyPy' and sys.version_info[0] == 3 and os.name == 'nt'
PYPY3_WIN_M = 'https://foss.heptapod.net/pypy/pypy/-/issues/3323 and https://foss.heptapod.net/pypy/pypy/-/issues/3321'


def pytest_collection_modifyitems(config, items):
    skip_int = pytest.mark.skip(reason='integration tests not run')
    skip_other = pytest.mark.skip(reason='only integration tests are run')

    if config.getoption('--run-integration') and config.getoption('--only-integration'):  # pragma: no cover
        raise pytest.UsageError("--run-integration and --only-integration can't be used together, choose one")

    for item in items:
        is_integration_file = os.path.basename(item.location[0]) == 'test_integration.py'
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


@pytest.fixture
def packages_path():
    return os.path.realpath(os.path.join(__file__, '..', 'packages'))


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
        from build.env import fs_supports_symlink

        if fs_supports_symlink():
            os.symlink(self_source, self_dest)
        else:  # pragma: no cover
            os.makedirs(self_dest)
            for target in ('pyproject.toml', 'setup.cfg', 'LICENSE', 'src'):
                target_source = os.path.join(self_source, target)
                target_dest = os.path.join(self_dest, target)
                if os.path.isfile(target_source):
                    shutil.copyfile(target_source, target_dest)
                else:
                    shutil.copytree(target_source, target_dest)

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
        """
        For some reason in some cases we don't have permission to remove
        symlinks on windows, even though we created them?
        """


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
