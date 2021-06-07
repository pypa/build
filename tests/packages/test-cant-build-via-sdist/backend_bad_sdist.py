# SPDX-License-Identifier: MIT

import os.path
import tarfile
import zipfile


def build_sdist(sdist_directory, config_settings=None):
    name = 'test_cant_build_via_sdist-1.0.0'
    file = '{}.tar.gz'.format(name)
    with tarfile.open(os.path.join(sdist_directory, file), 'w') as t:
        t.add('pyproject.toml', '{}/pyproject.toml'.format(name))
        t.add('backend_bad_sdist.py', '{}/backend_bad_sdist.py'.format(name))
    return file


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    if not os.path.isfile('some-file-that-is-needed-for-build.txt'):
        raise FileNotFoundError('some-file-that-is-needed-for-build.txt is missing!')
    # pragma: no cover
    file = 'test_cant_build_via_sdist-1.0.0-py2.py3-none-any.whl'
    zipfile.ZipFile(os.path.join(wheel_directory, file), 'w').close()
    return file
