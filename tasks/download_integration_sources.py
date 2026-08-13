"""Pre-downloads the integration test sources so the CI matrix shares one copy.

Reads ``INTEGRATION_SOURCES`` from ``tests/test_integration.py`` with ``ast`` to keep one list of projects. This is a
best effort task: a source that does not download is reported but does not fail the job, because the test fixture
downloads it too.

"""

from __future__ import annotations

import ast
import os
import shutil
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import cast


ROOT_SRC_DIR = Path(__file__).resolve().parents[1]
TEST_FILE = ROOT_SRC_DIR / 'tests' / 'test_integration.py'
STORE_DIR = ROOT_SRC_DIR / '.integration-sources'
ATTEMPTS = 3


def read_sources() -> dict[str, tuple[str, str]]:
    """Extract INTEGRATION_SOURCES without an import of the test module."""
    tree = ast.parse(TEST_FILE.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == 'INTEGRATION_SOURCES' for target in node.targets
        ):
            return cast('dict[str, tuple[str, str]]', ast.literal_eval(node.value))
    msg = f'INTEGRATION_SOURCES not found in {TEST_FILE}'
    raise SystemExit(msg)


def download(url: str, target: Path) -> None:
    """Download to a temporary name, then rename, so a partial file is never shared."""
    partial = target.with_suffix('.part')
    with urllib.request.urlopen(url) as request, partial.open('wb') as file_handler:  # noqa: S310
        shutil.copyfileobj(request, file_handler)
    os.replace(partial, target)


def download_with_retries(url: str, target: Path) -> bool:
    """Download with a backoff, because GitHub can drop a large archive request."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            download(url, target)
        except (OSError, urllib.error.URLError) as exception:  # noqa: PERF203
            print(f'attempt {attempt}/{ATTEMPTS} failed for {url}: {exception}')
            if attempt < ATTEMPTS:
                time.sleep(2**attempt)
        else:
            return True
    return False


def main() -> None:
    STORE_DIR.mkdir(exist_ok=True)
    failed = []
    for name, (github_org_repo, version) in read_sources().items():
        target = STORE_DIR / f'{name}-{version}.tar.gz'
        if target.exists():
            print(f'cached: {target.name}')
        elif download_with_retries(f'https://github.com/{github_org_repo}/archive/{version}.tar.gz', target):
            print(f'downloaded: {target.name}')
        else:
            failed.append(name)
    for partial in STORE_DIR.glob('*.part'):
        partial.unlink()
    if failed:
        print(f'::warning::could not pre-download {", ".join(failed)}; the tests download these themselves')


if __name__ == '__main__':
    main()
