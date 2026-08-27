# SPDX-License-Identifier: MIT

"""The projects that the integration tests build, and the cache of their archives.

``tests/test_integration.py`` imports this module, and CI runs it as a script to fill the cache once for the whole test
matrix. It uses the standard library only, so CI can run it before an install.

"""

from __future__ import annotations

import http.client
import os
import shutil
import time
import typing
import urllib.request

from pathlib import Path


INTEGRATION_SOURCES: dict[str, tuple[str, str]] = {
    'dateutil': ('dateutil/dateutil', '2.9.0'),
    'pip': ('pypa/pip', '25.0.1'),
    'Solaar': ('pwr-Solaar/Solaar', '1.1.14'),
    'flit': ('pypa/flit', '3.12.0'),
}

STORE_DIR = Path(__file__).resolve().parents[1] / '.integration-sources'
ATTEMPTS = 3
NETWORK_ERRORS = (OSError, http.client.HTTPException)


def download_archive(name: str) -> tuple[Path, str]:
    """Put the archive in the cache and return its path and version. Hold a lock around this to make it parallel safe."""
    github_org_repo, version = INTEGRATION_SOURCES[name]
    target = STORE_DIR / f'{name}-{version}.tar.gz'
    if target.exists():
        return target, version

    url = f'https://github.com/{github_org_repo}/archive/{version}.tar.gz'
    STORE_DIR.mkdir(exist_ok=True)
    # write to a temporary name, because GitHub can drop a large archive request and leave a truncated file behind
    partial = target.with_suffix('.part')
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url) as request, partial.open('wb') as file_handler:
                shutil.copyfileobj(typing.cast(http.client.HTTPResponse, request), file_handler)
        except NETWORK_ERRORS as exception:  # noqa: PERF203
            partial.unlink(missing_ok=True)
            if attempt == ATTEMPTS:
                raise
            print(f'attempt {attempt}/{ATTEMPTS} failed for {url}: {exception}')
            time.sleep(2**attempt)
        else:
            break
    os.replace(partial, target)
    return target, version


def main() -> None:
    failed = []
    for name in INTEGRATION_SOURCES:
        try:
            print(f'ready: {download_archive(name)[0].name}')
        except NETWORK_ERRORS as exception:  # noqa: PERF203
            print(f'failed: {name}: {exception}')
            failed.append(name)
    if failed:
        print(f'::warning::could not pre-download {", ".join(failed)}; the tests download these themselves')


if __name__ == '__main__':
    main()
