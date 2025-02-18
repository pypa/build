# SPDX-License-Identifier: MIT

import os.path
import tarfile
import zipfile


def build_sdist(sdist_directory, config_settings=None):
    name = 'test_cant_build_via_sdist-1.0.0'
    file = f'{name}.tar.gz'
    with tarfile.open(os.path.join(sdist_directory, file), 'w') as t:
        t.add('pyproject.toml', f'{name}/pyproject.toml')
        t.add('backend_bad_sdist.py', f'{name}/backend_bad_sdist.py')
    return file


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    if not os.path.isfile('some-file-that-is-needed-for-build.txt'):
        msg = 'some-file-that-is-needed-for-build.txt is missing!'
        raise FileNotFoundError(msg)
    # pragma: no cover
    file = 'test_cant_build_via_sdist-1.0.0-py3-none-any.whl'
    zipfile.ZipFile(os.path.join(wheel_directory, file), 'w').close()
    return file
