from __future__ import annotations

import pytest

from build.__main__ import _natural_language_list


def test_natural_language_list():
    assert _natural_language_list(['one']) == 'one'
    assert _natural_language_list(['one', 'two']) == 'one and two'
    assert _natural_language_list(['one', 'two', 'three']) == 'one, two and three'
    with pytest.raises(IndexError, match='no elements'):
        _natural_language_list([])
