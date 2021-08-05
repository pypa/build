# SPDX-License-Identifier: MIT

import os
import pathlib
import sys
import tempfile

from typing import Union

import pep517

import build
import build.env


if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


def _project_wheel_metadata(builder: build.ProjectBuilder) -> 'importlib_metadata.PackageMetadata':
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(builder.metadata_path(tmpdir))
        # https://github.com/python/importlib_metadata/pull/343
        return importlib_metadata.PathDistribution(path).metadata  # type: ignore


def project_wheel_metadata(
    srcdir: Union[str, 'os.PathLike[str]'],
    isolated: bool = True,
) -> 'importlib_metadata.PackageMetadata':
    """
    Return the wheel metadata for a project.

    Uses the ``prepare_metadata_for_build_wheel`` hook if availablable,
    otherwise ``build_wheel``.

    :param srcdir: Project source directory
    :param isolated: Wether or not to run invoke the backend in the current
                     environment or to create an isolated one and invoke it
                     there.
    """
    builder = build.ProjectBuilder(
        os.fspath(srcdir),
        runner=pep517.quiet_subprocess_runner,
    )

    if not isolated:
        return _project_wheel_metadata(builder)

    with build.env.IsolatedEnvBuilder() as env:
        builder.python_executable = env.executable
        builder.scripts_dir = env.scripts_dir
        env.install(builder.build_system_requires)
        env.install(builder.get_requires_for_build('wheel'))
        return _project_wheel_metadata(builder)


__all__ = ('project_wheel_metadata',)
