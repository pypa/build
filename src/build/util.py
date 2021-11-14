# SPDX-License-Identifier: MIT

import contextlib
import os
import sys
import tempfile

from typing import Iterator, Optional, Tuple

from . import ProjectBuilder
from ._helpers import PathType, quiet_runner
from .env import IsolatedEnvManager


if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


def _read_files(path: str) -> Iterator[Tuple[str, bytes]]:
    for dir_entry in os.scandir(path):
        if dir_entry.is_file():
            with open(dir_entry.path, 'rb') as file:
                yield (dir_entry.path, file.read())
        elif dir_entry.is_dir():
            yield from _read_files(dir_entry.path)


class _InMemoryDistribution(importlib_metadata.Distribution):
    def __init__(self, metadata_path: str) -> None:
        self._files = {os.path.relpath(p, metadata_path): f for p, f in _read_files(metadata_path)}

    def read_text(self, filename: str) -> str:
        return self._files[filename].decode()

    def locate_file(self, path: PathType) -> 'os.PathLike[str]':
        raise NotImplementedError


def project_wheel_metadata(srcdir: PathType, isolated: bool = True) -> importlib_metadata.Distribution:
    """
    Return the wheel metadata for a project.

    Uses the ``prepare_metadata_for_build_wheel`` hook if available,
    otherwise ``build_wheel``.

    :param srcdir: Project source directory
    :param isolated: Whether to invoke the backend in the current environment
        or create an isolated environment and invoke it there
    """

    @contextlib.contextmanager
    def prepare_builder() -> Iterator[ProjectBuilder]:
        if not isolated:
            yield ProjectBuilder(srcdir, runner=quiet_runner)
            return

        with IsolatedEnvManager() as env:
            builder = ProjectBuilder.from_isolated_env(env, srcdir, runner=quiet_runner)
            env.install_packages(builder.build_system_requires)
            env.install_packages(builder.get_requires_for_build('wheel'))
            yield builder

    with prepare_builder() as builder, tempfile.TemporaryDirectory(prefix='build-wheel-metadata-') as temp_dir:
        return _InMemoryDistribution(builder.metadata_path(temp_dir))


__all__ = [
    'project_wheel_metadata',
]
