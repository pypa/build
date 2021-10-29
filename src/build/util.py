# SPDX-License-Identifier: MIT

import pathlib
import sys
import tempfile

import pep517

from . import PathType, ProjectBuilder
from .env import IsolatedEnvManager


if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


def _project_wheel_metadata(builder: ProjectBuilder) -> 'importlib_metadata.PackageMetadata':
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(builder.metadata_path(tmpdir))
        # https://github.com/python/importlib_metadata/pull/343
        return importlib_metadata.PathDistribution(path).metadata  # type: ignore


def project_wheel_metadata(
    srcdir: PathType,
    isolated: bool = True,
) -> 'importlib_metadata.PackageMetadata':
    """
    Return the wheel metadata for a project.

    Uses the ``prepare_metadata_for_build_wheel`` hook if available,
    otherwise ``build_wheel``.

    :param srcdir: Project source directory
    :param isolated: Whether or not to run invoke the backend in the current
                     environment or to create an isolated one and invoke it
                     there.
    """
    if not isolated:
        builder = ProjectBuilder(srcdir, runner=pep517.quiet_subprocess_runner)
        return _project_wheel_metadata(builder)

    with IsolatedEnvManager() as env:
        builder = ProjectBuilder.from_isolated_env(env, srcdir)
        env.install_packages(builder.build_system_requires)
        env.install_packages(builder.get_requires_for_build('wheel'))
        return _project_wheel_metadata(builder)


__all__ = [
    'project_wheel_metadata',
]
