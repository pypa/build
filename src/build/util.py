# SPDX-License-Identifier: MIT

import pathlib
import sys
import tempfile

from . import ProjectBuilder
from ._helpers import PathType, quiet_runner
from .env import IsolatedEnvManager


if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


def _project_wheel_metadata(builder: ProjectBuilder) -> 'importlib_metadata.PackageMetadata':
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(builder.metadata_path(tmpdir))
        # https://github.com/python/importlib_metadata/pull/342
        return importlib_metadata.PathDistribution(path).metadata  # type: ignore[arg-type]


def project_wheel_metadata(
    srcdir: PathType,
    isolated: bool = True,
) -> 'importlib_metadata.PackageMetadata':
    """
    Return the wheel metadata for a project.

    Uses the ``prepare_metadata_for_build_wheel`` hook if available,
    otherwise ``build_wheel``.

    :param srcdir: Project source directory
    :param isolated: Whether to invoke the backend in the current environment
        or create an isolated environment and invoke it there
    """
    if not isolated:
        builder = ProjectBuilder(srcdir, runner=quiet_runner)
        return _project_wheel_metadata(builder)

    with IsolatedEnvManager() as env:
        builder = ProjectBuilder.from_isolated_env(env, srcdir, runner=quiet_runner)
        env.install_packages(builder.build_system_requires)
        env.install_packages(builder.get_requires_for_build('wheel'))
        return _project_wheel_metadata(builder)


__all__ = [
    'project_wheel_metadata',
]
