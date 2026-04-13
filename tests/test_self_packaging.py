# These tests check the sdist, path, and wheel of build to ensure that all are valid.

from __future__ import annotations

import subprocess
import sys
import tarfile
import zipfile

from pathlib import Path, PurePosixPath

import pytest


DIR = Path(__file__).parent.resolve()
MAIN_DIR = DIR.parent


sdist_files = {
    '.dockerignore',
    '.gitignore',
    'CHANGELOG.rst',
    'LICENSE',
    'PKG-INFO',
    'README.md',
    'docs/conf.py',
    'pyproject.toml',
    'src/build/py.typed',
    'tests/constraints.txt',
    'tests/packages/test-cant-build-via-sdist/some-file-that-is-needed-for-build.txt',
    'tests/packages/test-no-project/empty.txt',
    'tests/packages/test-setuptools/MANIFEST.in',
    'tox.toml',
}

sdist_patterns = {
    'docs/*.rst',
    'docs/*/*.rst',
    'docs/_static/*',
    'src/build/*.py',
    'src/build/_compat/*.py',
    'tests/*.py',
    'tests/packages/*/*.py',
    'tests/packages/*/*/*.py',
    'tests/packages/*/pyproject.toml',
    'tests/packages/*/setup.*',
}

sdist_files |= {str(PurePosixPath(p.relative_to(MAIN_DIR))) for path in sdist_patterns for p in MAIN_DIR.glob(path)}

wheel_files = {
    'build/__init__.py',
    'build/__main__.py',
    'build/_builder.py',
    'build/_compat/__init__.py',
    'build/_compat/importlib.py',
    'build/_compat/tarfile.py',
    'build/_compat/tomllib.py',
    'build/_ctx.py',
    'build/_exceptions.py',
    'build/_types.py',
    'build/_util.py',
    'build/env.py',
    'build/py.typed',
    'build/util.py',
    'dist-info/licenses/LICENSE',
    'dist-info/METADATA',
    'dist-info/RECORD',
    'dist-info/WHEEL',
    'dist-info/entry_points.txt',
}


@pytest.mark.network
def test_build_sdist(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(MAIN_DIR)

    subprocess.run(
        [
            sys.executable,
            '-m',
            'build',
            '--sdist',
            '--outdir',
            str(tmp_path),
        ],
        check=True,
    )

    (sdist,) = tmp_path.glob('*.tar.gz')

    with tarfile.open(str(sdist), 'r:gz') as tar:
        simpler = {n.split('/', 1)[-1] for n in tar.getnames() if '/__pycache__/' not in n}

    assert simpler == sdist_files


@pytest.mark.network
@pytest.mark.parametrize('args', [(), ('--wheel',)], ids=('from_sdist', 'direct'))
def test_build_wheel(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, args: tuple[str, ...]) -> None:
    monkeypatch.chdir(MAIN_DIR)

    subprocess.run(
        [
            sys.executable,
            '-m',
            'build',
            *args,
            '--outdir',
            str(tmp_path),
        ],
        check=True,
    )

    (wheel,) = tmp_path.glob('*.whl')

    with zipfile.ZipFile(str(wheel)) as z:
        names = z.namelist()

    trimmed = {n for n in names if 'dist-info' not in n}
    trimmed |= {f'dist-info/{n.split("/", 1)[-1]}' for n in names if 'dist-info' in n}

    assert trimmed == wheel_files
