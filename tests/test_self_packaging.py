# These tests check the sdist, path, and wheel of build to ensure that all are valid.

import subprocess
import sys
import tarfile
import zipfile

from pathlib import Path

import pytest


DIR = Path(__file__).parent.resolve()
MAIN_DIR = DIR.parent

sdist_files = {
    'LICENSE',
    'PKG-INFO',
    'README.md',
    'pyproject.toml',
    'src/build/__init__.py',
    'src/build/__main__.py',
    'src/build/_exceptions.py',
    'src/build/_importlib.py',
    'src/build/_util.py',
    'src/build/env.py',
    'src/build/py.typed',
    'src/build/util.py',
}

wheel_files = {
    'build/__init__.py',
    'build/__main__.py',
    'build/_exceptions.py',
    'build/_importlib.py',
    'build/_util.py',
    'build/env.py',
    'build/py.typed',
    'build/util.py',
    'dist-info/LICENSE',
    'dist-info/METADATA',
    'dist-info/RECORD',
    'dist-info/WHEEL',
    'dist-info/entry_points.txt',
}


def test_build_sdist(monkeypatch, tmpdir):
    monkeypatch.chdir(MAIN_DIR)

    subprocess.run(
        [
            sys.executable,
            '-m',
            'build',
            '--sdist',
            '--outdir',
            str(tmpdir),
        ],
        check=True,
    )

    (sdist,) = tmpdir.visit('*.tar.gz')

    with tarfile.open(str(sdist), 'r:gz') as tar:
        simpler = {n.split('/', 1)[-1] for n in tar.getnames()}

    assert simpler == sdist_files


@pytest.mark.parametrize('args', ((), ('--wheel',)), ids=('from_sdist', 'direct'))
def test_build_wheel(monkeypatch, tmpdir, args):
    monkeypatch.chdir(MAIN_DIR)

    subprocess.run(
        [
            sys.executable,
            '-m',
            'build',
            *args,
            '--outdir',
            str(tmpdir),
        ],
        check=True,
    )

    (wheel,) = tmpdir.visit('*.whl')

    with zipfile.ZipFile(str(wheel)) as z:
        names = z.namelist()

    trimmed = {n for n in names if 'dist-info' not in n}
    trimmed |= {f"dist-info/{n.split('/', 1)[-1]}" for n in names if 'dist-info' in n}

    assert trimmed == wheel_files
