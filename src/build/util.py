# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import pathlib
import sys
import tempfile

import pyproject_hooks

import build
import build.env


if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


def _project_wheel_metadata(builder: build.ProjectBuilder) -> importlib_metadata.PackageMetadata:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(builder.metadata_path(tmpdir))
        return importlib_metadata.PathDistribution(path).metadata


def project_wheel_metadata(
    srcdir: build.PathType,
    isolated: bool = True,
    runner: build.RunnerType = pyproject_hooks.quiet_subprocess_runner,
) -> importlib_metadata.PackageMetadata:
    """
    Return the wheel metadata for a project.

    Uses the ``prepare_metadata_for_build_wheel`` hook if available,
    otherwise ``build_wheel``.

    :param srcdir: Project source directory
    :param isolated: Whether or not to run invoke the backend in the current
                     environment or to create an isolated one and invoke it
                     there.
    :param runner: An alternative runner for backend subprocesses
    """
    builder = build.ProjectBuilder(
        os.fspath(srcdir),
        runner=runner,
    )

    if not isolated:
        return _project_wheel_metadata(builder)

    with build.env.IsolatedEnvBuilder() as env:
        builder.python_executable = env.executable
        builder.scripts_dir = env.scripts_dir
        env.install(builder.build_system_requires)
        env.install(builder.get_requires_for_build('wheel'))
        return _project_wheel_metadata(builder)


__all__ = [
    'project_wheel_metadata',
]
