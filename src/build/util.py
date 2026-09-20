# SPDX-License-Identifier: MIT

from __future__ import annotations


__lazy_modules__ = {
    'packaging',
    'packaging.metadata',
    'pathlib',
    'tempfile',
    f'{__spec__.parent}._compat',
    f'{__spec__.parent}._exceptions',
    f'{__spec__.parent}.env',
}

import pathlib
import tempfile

import packaging.metadata
import pyproject_hooks

from . import ProjectBuilder
from ._compat import importlib
from ._exceptions import DependencyError
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


def _wheel_metadata(builder: ProjectBuilder) -> packaging.metadata.RawMetadata:
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata = pathlib.Path(builder.metadata_path(tmpdir), 'METADATA').read_bytes()
    parsed, _ = packaging.metadata.parse_email(metadata)
    return parsed


def wheel_metadata(
    source_dir: StrPath,
    isolated: bool = True,
    *,
    runner: SubprocessRunner = pyproject_hooks.quiet_subprocess_runner,
    check_dependencies: bool = False,
) -> packaging.metadata.RawMetadata:
    """
    Return a project's wheel metadata as a parsed, JSON-serialisable mapping.

    Uses the ``prepare_metadata_for_build_wheel`` hook if available, otherwise
    ``build_wheel``, and parses the resulting ``METADATA`` the same way as the
    ``python -m build --metadata`` command.

    :param source_dir: Project source directory
    :param isolated: Whether or not to invoke the backend in the current
                     environment or to create an isolated one and invoke it
                     there.
    :param runner: An alternative runner for backend subprocesses
    :param check_dependencies: When not isolated, verify that the project's
                               declared build dependencies are installed in the
                               current environment before invoking the backend.
                               Ignored when ``isolated`` is true.
    :raises DependencyError: If dependency checking is enabled and any declared
                             build dependency is not satisfied.
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
            return _wheel_metadata(builder)

    builder = ProjectBuilder(
        source_dir,
        runner=runner,
    )
    if check_dependencies and (unmet := builder.check_dependencies('wheel')):
        raise DependencyError(unmet)

    return _wheel_metadata(builder)


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

    :param source_dir: Project source directory
    :param isolated: Whether or not to run invoke the backend in the current
                     environment or to create an isolated one and invoke it
                     there.
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
    else:
        builder = ProjectBuilder(
            source_dir,
            runner=runner,
        )
        return _project_wheel_metadata(builder)


__all__ = [
    'project_wheel_metadata',
    'wheel_metadata',
]
