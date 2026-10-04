from __future__ import annotations


__lazy_modules__ = {'pathlib', 'tarfile'}

import sys
import tarfile

from pathlib import Path


# Per https://peps.python.org/pep-0706/, the "data" filter became the default
# in Python 3.14. The first series of releases with the filter had a broken
# filter that could not process symlinks correctly, so the patch releases that
# fixed it are the lower bounds here.
_HAS_DATA_FILTER = (
    (3, 10, 13) <= sys.version_info < (3, 11) or (3, 11, 5) <= sys.version_info < (3, 12) or sys.version_info >= (3, 12)
)


# On runtimes that ship the stdlib ``data`` filter we delegate to it; the fallback branch is
# only reached on 3.10.0-3.10.12 / 3.11.0-3.11.4 and validates each member manually before extraction.
if _HAS_DATA_FILTER:

    def safe_extractall(tar: tarfile.TarFile, path: Path | str) -> None:  # pragma: no cover
        """Extract every member of ``tar`` into ``path`` via the PEP 706 ``data`` filter."""
        tar.extractall(path, filter='data')

    def _accept_member(member: tarfile.TarInfo, path: Path | str) -> None:  # pragma: no cover
        tarfile.data_filter(member, str(path))

else:

    def safe_extractall(tar: tarfile.TarFile, path: Path | str) -> None:  # pragma: no cover
        """Validate every member of ``tar``, then extract into ``path``.

        Reached on 3.10.0-3.10.12 / 3.11.0-3.11.4 where the stdlib ``data`` filter is missing. Device or special files,
        paths that escape ``path``, and symlinks/hardlinks whose targets resolve outside ``path`` are rejected before
        any write hits the disk.

        """
        base = Path(path).resolve()
        for member in tar.getmembers():
            _validate_safe_member(member, base)
        tar.extractall(path)  # noqa: S202

    def _accept_member(member: tarfile.TarInfo, path: Path | str) -> None:  # pragma: no cover
        _validate_safe_member(member, Path(path).resolve())


def check_extractable(tar: tarfile.TarFile, path: Path | str) -> None:
    """Reject every member of ``tar`` that :func:`safe_extractall` would refuse, without extracting anything.

    This asks the same rule :func:`safe_extractall` applies rather than re-deriving it, so the verdict here is exactly
    the one extraction will reach. Useful before acting on an archive's contents, when nothing has been written yet and
    a refusal costs nothing.

    """
    for member in tar.getmembers():
        _accept_member(member, path)


def _validate_safe_member(member: tarfile.TarInfo, base: Path) -> None:
    if member.ischr() or member.isblk() or member.isfifo():
        msg = f'refusing to extract special device file {member.name!r}'
        raise tarfile.TarError(msg)
    target = (base / member.name).resolve(strict=False)
    if not target.is_relative_to(base):
        msg = f'refusing to extract {member.name!r}: path escapes destination'
        raise tarfile.TarError(msg)
    if member.issym() or member.islnk():
        link_base = target.parent if member.issym() else base
        link_target = (link_base / member.linkname).resolve(strict=False)
        if not link_target.is_relative_to(base):
            msg = f'refusing to extract {member.name!r}: link target escapes destination'
            raise tarfile.TarError(msg)


__all__ = [
    'check_extractable',
    'safe_extractall',
]
