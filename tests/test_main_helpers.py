from __future__ import annotations

import pathlib

import pytest

from build.__main__ import _natural_language_list, _parse_constraints_txt


def test_natural_language_list() -> None:
    assert _natural_language_list(['one']) == 'one'
    assert _natural_language_list(['one', 'two']) == 'one and two'
    assert _natural_language_list(['one', 'two', 'three']) == 'one, two and three'
    with pytest.raises(IndexError, match='no elements'):
        _natural_language_list([])


def test_parse_constraints_txt_single_line(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'constraints.txt'
    path.write_text('foo==1.0\nbar==2.0\n', encoding='utf-8')
    assert _parse_constraints_txt(path) == {'foo==1.0', 'bar==2.0'}


def test_parse_constraints_txt_ignores_comments_and_blank_lines(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'constraints.txt'
    path.write_text('# a comment\nfoo==1.0\n\nbar==2.0\n', encoding='utf-8')
    assert _parse_constraints_txt(path) == {'foo==1.0', 'bar==2.0'}


def test_parse_constraints_txt_joins_backslash_continuations(tmp_path: pathlib.Path) -> None:
    # As produced by e.g. `pip-compile --generate-hashes`: a requirement and its
    # --hash options wrapped onto continuation lines. Regression test for the
    # requirement/hash pair being split apart and losing its hash when the file
    # is later reconstructed from a set of independently-parsed physical lines.
    path = tmp_path / 'constraints.txt'
    path.write_text(
        'editables==0.6 \\\n'
        '    --hash=sha256:1163834902381c4613787951c5914800fdf155ae08848a373b8ea5006780977c \\\n'
        '    --hash=sha256:d70e4698078a1d033e7786d9c64e5be070d058a67c21417024d38a58ac20aa43\n'
        '    # via reprodemo (pyproject.toml::build-system.backend::editable)\n'
        'hatchling==1.31.0 \\\n'
        '    --hash=sha256:6b48ad4068a482ed7239b3a8215bc55b47aad3345d58dfc94e553c5d2d46211b \\\n'
        '    --hash=sha256:aac80bec8b6fe35e8480f1c335be8910fa210a0e6f735a139be205dadcacb544\n'
        '    # via reprodemo (pyproject.toml::build-system.requires)\n',
        encoding='utf-8',
    )
    editables_line = (
        'editables==0.6 '
        '--hash=sha256:1163834902381c4613787951c5914800fdf155ae08848a373b8ea5006780977c '
        '--hash=sha256:d70e4698078a1d033e7786d9c64e5be070d058a67c21417024d38a58ac20aa43'
    )
    hatchling_line = (
        'hatchling==1.31.0 '
        '--hash=sha256:6b48ad4068a482ed7239b3a8215bc55b47aad3345d58dfc94e553c5d2d46211b '
        '--hash=sha256:aac80bec8b6fe35e8480f1c335be8910fa210a0e6f735a139be205dadcacb544'
    )
    assert _parse_constraints_txt(path) == {editables_line, hatchling_line}
