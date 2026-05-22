# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from tarfile import CHRTYPE, LNKTYPE, SYMTYPE, TarError, TarInfo
from tarfile import open as tar_open

import pytest

from build._compat.tarfile import _validate_safe_member, safe_extractall


FileMember = Callable[[str, bytes], TarInfo]
LinkMember = Callable[..., TarInfo]
DeviceMember = Callable[[str], TarInfo]
ArchiveBuilder = Callable[[Path, 'list[tuple[TarInfo, bytes | None]]'], None]


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
