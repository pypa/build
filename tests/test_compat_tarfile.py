# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from tarfile import CHRTYPE, LNKTYPE, SYMTYPE, TarError, TarInfo
from tarfile import open as tar_open
from typing import Protocol

import pytest

from build._compat.tarfile import (
    _HAS_DATA_FILTER,
    _validate_safe_member,
    extractable_member_names,
    safe_extractall,
)


FileMember = Callable[[str, bytes], TarInfo]
DeviceMember = Callable[[str], TarInfo]
ArchiveBuilder = Callable[[Path, 'list[tuple[TarInfo, bytes | None]]'], None]


class LinkMember(Protocol):
    def __call__(self, name: str, linkname: str, *, hard: bool = ...) -> TarInfo: ...


def test_safe_extractall_extracts_clean_archive(
    tmp_path: Path,
    make_archive: ArchiveBuilder,
    file_member: FileMember,
) -> None:
    archive = tmp_path / 'clean.tar'
    body = b'meta'
    make_archive(archive, [(file_member('pkg/PKG-INFO', body), body)])

    out = tmp_path / 'out'
    out.mkdir()
    with tar_open(archive) as tar:
        safe_extractall(tar, str(out))

    assert (out / 'pkg' / 'PKG-INFO').read_bytes() == body


def test_validate_safe_member_accepts_clean_file(tmp_path: Path, file_member: FileMember) -> None:
    base = tmp_path.resolve()
    _validate_safe_member(file_member('pkg/file.txt', b'x'), base)


def test_validate_safe_member_rejects_path_traversal(tmp_path: Path, file_member: FileMember) -> None:
    base = tmp_path.resolve()
    with pytest.raises(TarError, match='escapes destination'):
        _validate_safe_member(file_member('../evil.txt', b'x'), base)


def test_validate_safe_member_rejects_absolute_symlink(tmp_path: Path, link_member: LinkMember) -> None:
    base = tmp_path.resolve()
    with pytest.raises(TarError, match='link target escapes'):
        _validate_safe_member(link_member('pkg/evil', '/etc/passwd'), base)


def test_validate_safe_member_rejects_relative_escape_symlink(tmp_path: Path, link_member: LinkMember) -> None:
    base = tmp_path.resolve()
    with pytest.raises(TarError, match='link target escapes'):
        _validate_safe_member(link_member('pkg/evil', '../../outside'), base)


def test_validate_safe_member_accepts_safe_symlink(tmp_path: Path, link_member: LinkMember) -> None:
    base = tmp_path.resolve()
    _validate_safe_member(link_member('pkg/link', 'real.txt'), base)


def test_validate_safe_member_rejects_escaping_hardlink(tmp_path: Path, link_member: LinkMember) -> None:
    base = tmp_path.resolve()
    with pytest.raises(TarError, match='link target escapes'):
        _validate_safe_member(link_member('pkg/evil', '../../outside', hard=True), base)


def test_validate_safe_member_rejects_device_file(tmp_path: Path, device_member: DeviceMember) -> None:
    base = tmp_path.resolve()
    with pytest.raises(TarError, match='special device file'):
        _validate_safe_member(device_member('pkg/null'), base)


@pytest.mark.parametrize(
    'name',
    [
        pytest.param('pkg/file.txt', id='plain'),
        pytest.param('pkg/nested/deep.txt', id='nested'),
        pytest.param('./pkg-1.0/file.txt', id='leading-dot'),
    ],
)
def test_extractable_member_names_returns_the_written_names(
    tmp_path: Path,
    make_archive: ArchiveBuilder,
    file_member: FileMember,
    name: str,
) -> None:
    """A name the filter keeps comes back unchanged, so the caller can reason about where files land."""
    archive = tmp_path / 'ok.tar'
    make_archive(archive, [(file_member(name, b'x'), b'x')])

    with tar_open(archive) as tar:
        assert extractable_member_names(tar, tmp_path / 'out') == [name]


def test_extractable_member_names_absolute_member_rewritten(
    tmp_path: Path,
    make_archive: ArchiveBuilder,
    file_member: FileMember,
) -> None:
    """The two branches disagree about an absolute member, and only one of them hands back a name.

    The stdlib filter does not refuse a leading separator, it drops it, so ``/etc/evil.txt`` is rewritten to
    ``etc/evil.txt`` and lands inside the destination -- which is why the name has to come from the filter's output. The
    pre-filter fallback refuses it outright instead. Written as one test that runs on both, because this suite is
    measured for 100% coverage and a test skipped on the current interpreter is a hole on it.

    """
    archive = tmp_path / 'absolute.tar'
    make_archive(archive, [(file_member('/etc/evil.txt', b'x'), b'x')])

    with tar_open(archive) as tar:
        if _HAS_DATA_FILTER:
            assert extractable_member_names(tar, tmp_path / 'out') == ['etc/evil.txt']
        else:  # pragma: no cover - the fallback is what the older matrix jobs measure
            with pytest.raises(TarError, match='escapes destination'):
                extractable_member_names(tar, tmp_path / 'out')


def test_extractable_member_names_rejects_traversal(
    tmp_path: Path,
    make_archive: ArchiveBuilder,
    file_member: FileMember,
) -> None:
    archive = tmp_path / 'traversal.tar'
    make_archive(archive, [(file_member('../evil.txt', b'x'), b'x')])

    with tar_open(archive) as tar, pytest.raises(TarError):
        extractable_member_names(tar, tmp_path / 'out')


def test_extractable_member_names_rejects_traversal_behind_dot(
    tmp_path: Path,
    make_archive: ArchiveBuilder,
    file_member: FileMember,
) -> None:
    """``realpath`` folds the ``.`` away first, so this escapes just like a bare ``..`` does."""
    archive = tmp_path / 'dotdot.tar'
    make_archive(archive, [(file_member('./../evil.txt', b'x'), b'x')])

    with tar_open(archive) as tar, pytest.raises(TarError):
        extractable_member_names(tar, tmp_path / 'out')


def test_extractable_member_names_rejects_device_file(
    tmp_path: Path,
    make_archive: ArchiveBuilder,
    device_member: DeviceMember,
) -> None:
    archive = tmp_path / 'device.tar'
    make_archive(archive, [(device_member('pkg/null'), None)])

    with tar_open(archive) as tar, pytest.raises(TarError):
        extractable_member_names(tar, tmp_path / 'out')


def test_extractable_member_names_rejects_escaping_symlink(
    tmp_path: Path,
    make_archive: ArchiveBuilder,
    link_member: LinkMember,
) -> None:
    archive = tmp_path / 'symlink.tar'
    make_archive(archive, [(link_member('pkg/evil', '../../outside'), None)])

    with tar_open(archive) as tar, pytest.raises(TarError):
        extractable_member_names(tar, tmp_path / 'out')


def test_extractable_member_names_predicts_where_extraction_lands(
    tmp_path: Path,
    make_archive: ArchiveBuilder,
    file_member: FileMember,
) -> None:
    """Every returned name is a real path under the destination once the extraction has run.

    This is the property the caller relies on: a name it was handed is a file that then exists, so it can act on the
    name (delete it, descend into it) without re-deriving tarfile's rules.

    """
    archive = tmp_path / 'agree.tar'
    body = b'meta'
    names = ('pkg/PKG-INFO', 'pkg/nested/inner.txt')
    make_archive(archive, [(file_member(name, body), body) for name in names])

    out = tmp_path / 'out'
    out.mkdir()
    with tar_open(archive) as tar:
        reported = extractable_member_names(tar, out)
        safe_extractall(tar, out)

    assert reported == list(names)
    for name in reported:
        assert (out / name).is_file(), f'{name} was reported but never written'


@pytest.fixture
def make_archive() -> ArchiveBuilder:
    def _build(path: Path, members: list[tuple[TarInfo, bytes | None]]) -> None:
        with tar_open(path, 'w') as tar:
            for info, body in members:
                tar.addfile(info, BytesIO(body) if body is not None else None)

    return _build


@pytest.fixture
def file_member() -> FileMember:
    def _build(name: str, body: bytes) -> TarInfo:
        info = TarInfo(name=name)
        info.size = len(body)
        return info

    return _build


@pytest.fixture
def link_member() -> LinkMember:
    def _build(name: str, linkname: str, *, hard: bool = False) -> TarInfo:
        info = TarInfo(name=name)
        info.type = LNKTYPE if hard else SYMTYPE
        info.linkname = linkname
        return info

    return _build


@pytest.fixture
def device_member() -> DeviceMember:
    def _build(name: str) -> TarInfo:
        info = TarInfo(name=name)
        info.type = CHRTYPE
        info.devmajor = 1
        info.devminor = 3
        return info

    return _build
