# SPDX-License-Identifier: MIT

from __future__ import annotations

import importlib.util
import os
import os.path
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request

import filelock
import pytest

import build.__main__


IS_WINDOWS = sys.platform.startswith('win')
IS_PYPY = sys.implementation.name == 'pypy'
MISSING_UV = not shutil.which('uv')


INTEGRATION_SOURCES = {
    'dateutil': ('dateutil/dateutil', '2.9.0'),
    'pip': ('pypa/pip', '25.0.1'),
    'Solaar': ('pwr-Solaar/Solaar', '1.1.14'),
    'flit': ('pypa/flit', '3.12.0'),
}

_SDIST = re.compile('.*.tar.gz')
_WHEEL = re.compile('.*.whl')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCL = frozenset(['.tox', 'dist', '.git', '__pycache__', '.integration-sources', '.github', 'tests', 'docs'])


def get_project(name, tmp_path):
    dest = tmp_path / name
    if name == 'build':
        # our own project is available in-source, just ignore development files

        def _ignore_folder(base, filenames):
            ignore = [
                n for n in filenames if n in EXCL or n.endswith(('_cache', '.egg-info', '.pyc')) or n.startswith('.coverage')
            ]
            if os.path.basename(base) == ROOT and 'build' in filenames:  # ignore build only at root (our module is build too)
                ignore.append('build')
            return ignore

        shutil.copytree(ROOT, str(dest), ignore=_ignore_folder)
        return dest

    # for other projects download from github and cache it
    tar_store = os.path.join(ROOT, '.integration-sources')
    try:
        os.makedirs(tar_store)
    except OSError:  # python 2 has no exist_ok, and checking with exists is not parallel safe
        pass  # just ignore, if the creation failed we will have another failure soon that will notify the user

    github_org_repo, version = INTEGRATION_SOURCES[name]
    tar_filename = f'{name}-{version}.tar.gz'
    tarball = os.path.join(tar_store, tar_filename)
    with filelock.FileLock(os.path.join(tar_store, f'{tar_filename}.lock')):
        if not os.path.exists(tarball):
            url = f'https://github.com/{github_org_repo}/archive/{version}.tar.gz'
            with urllib.request.urlopen(url) as request, open(tarball, 'wb') as file_handler:
                shutil.copyfileobj(request, file_handler)
    with tarfile.open(tarball, 'r:gz') as tar_handler:
        tar_handler.extractall(str(dest))
    return dest / f'{name}-{version}'


@pytest.mark.network
@pytest.mark.parametrize(
    'call',
    [
        None,  # via code
        [sys.executable, '-m', 'build'],  # module
        ['pyproject-build'],  # entrypoint
    ],
    ids=['code', 'module', 'entrypoint'],
)
@pytest.mark.parametrize(
    'args',
    [
        [],
        pytest.param(
            ['--installer', 'uv'],
            marks=pytest.mark.skipif(MISSING_UV, reason='uv executable not found'),
        ),
        ['-x', '--no-isolation'],
    ],
    ids=['isolated_pip', 'isolated_uv', 'no_isolation'],
)
@pytest.mark.parametrize(
    'project',
    [
        'build',
        'pip',
        'dateutil',
        'Solaar',
        'flit',
    ],
)
@pytest.mark.isolated
def test_build(request, monkeypatch, project, args, call, tmp_path):
    if args == ['--installer', 'uv'] and IS_WINDOWS and IS_PYPY:
        pytest.xfail('uv cannot find PyPy executable')
    if project in {'build', 'flit'} and '--no-isolation' in args:
        pytest.xfail(f"can't build {project} without isolation due to missing dependencies")
    if project == 'Solaar' and IS_WINDOWS and IS_PYPY:
        pytest.xfail('Solaar fails building wheels via sdists on Windows on PyPy 3')

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('SETUPTOOLS_SCM_PRETEND_VERSION', '0+dummy')  # for the projects that use setuptools_scm

    if call and call[0] == 'pyproject-build':
        exe_name = f'pyproject-build{".exe" if sys.platform.startswith("win") else ""}'
        exe = os.path.join(os.path.dirname(sys.executable), exe_name)
        if os.path.exists(exe):
            call[0] = exe
        else:
            pytest.skip('Running via PYTHONPATH, so the pyproject-build entrypoint is not available')
    path = get_project(project, tmp_path)
    pkgs = tmp_path / 'pkgs'
    args = [str(path), '-o', str(pkgs), *args]

    if call is None:
        build.__main__.main(args)
    else:
        subprocess.check_call(call + args)

    pkg_names = os.listdir(str(pkgs))
    assert list(filter(_SDIST.match, pkg_names))
    assert list(filter(_WHEEL.match, pkg_names))


def test_isolation(tmp_dir, package_test_flit, mocker):
    if importlib.util.find_spec('flit_core'):
        pytest.xfail('flit_core is available -- we want it missing!')  # pragma: no cover

    mocker.patch('build.__main__._error')

    build.__main__.main([package_test_flit, '-o', tmp_dir, '--no-isolation'])
    build.__main__._error.assert_called_with("Backend 'flit_core.buildapi' is not available.")
