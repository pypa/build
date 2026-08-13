# SPDX-License-Identifier: MIT

from __future__ import annotations


__lazy_modules__ = [
    f'{__spec__.parent}._compat',
    f'{__spec__.parent}._exceptions',
    f'{__spec__.parent}._util',
    f'{__spec__.parent}.env',
    'pathlib',
    'tempfile',
    'warnings',
]

import pathlib
import tempfile
import warnings

import pyproject_hooks

from . import ProjectBuilder
from ._compat import importlib
from ._exceptions import BuildException
from ._util import format_unmet_dependencies
from .env import DefaultIsolatedEnv


TYPE_CHECKING = False
if TYPE_CHECKING:
    from ._types import StrPath, SubprocessRunner


def _project_wheel_metadata(builder: ProjectBuilder) -> importlib.metadata.PackageMetadata:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(builder.metadata_path(tmpdir))
        metadata = importlib.metadata.PathDistribution(path).metadata
        assert metadata is not None
        return metadata


def wheel_metadata(
    source_dir: StrPath,
    isolated: bool = True,
    *,
    check_dependencies: bool = True,
    runner: SubprocessRunner = pyproject_hooks.quiet_subprocess_runner,
) -> importlib.metadata.PackageMetadata:
    """
    Return the wheel metadata for a project.

    Uses the ``prepare_metadata_for_build_wheel`` hook if available,
    otherwise ``build_wheel``.

    :param source_dir: Project source directory
    :param isolated: Whether or not to run invoke the backend in the current
                     environment or to create an isolated one and invoke it
                     there.
    :param check_dependencies: Whether to verify that build dependencies are
                               available in non-isolated mode.
    :param runner: An alternative runner for backend subprocesses
    """
    if isolated:
        with DefaultIsolatedEnv() as env:
            builder = ProjectBuilder.from_isolated_env(
                env,
                source_dir,
                runner=runner,
            )
            env.install(builder.build_system_requires, _fresh=True)
            env.install(builder.get_requires_for_build('wheel'))
            return _project_wheel_metadata(builder)

    builder = ProjectBuilder(
        source_dir,
        runner=runner,
    )
    if check_dependencies and (missing := builder.check_dependencies('wheel')):
        raise BuildException(format_unmet_dependencies(missing))
    return _project_wheel_metadata(builder)


def project_wheel_metadata(
    source_dir: StrPath,
    isolated: bool = True,
    *,
    runner: SubprocessRunner = pyproject_hooks.quiet_subprocess_runner,
) -> importlib.metadata.PackageMetadata:
    """
    Return the wheel metadata for a project.

    Uses the ``prepare_metadata_for_build_wheel`` hook if available,
    otherwise ``build_wheel``.

    .. deprecated:: 1.6.0
       Use :func:`wheel_metadata` instead.

    :param source_dir: Project source directory
    :param isolated: Whether or not to run invoke the backend in the current
                     environment or to create an isolated one and invoke it
                     there.
    :param runner: An alternative runner for backend subprocesses
    """
    warnings.warn(
        'project_wheel_metadata is deprecated; use build.util.wheel_metadata instead',
        DeprecationWarning,
        stacklevel=2,
    )
    return wheel_metadata(
        source_dir,
        isolated=isolated,
        check_dependencies=False,
        runner=runner,
    )


__all__ = [
    'project_wheel_metadata',
    'wheel_metadata',
]
