# SPDX-License-Identifier: MIT

import sys

import pytest

import build


def test_version():
    assert build.__version__


@pytest.mark.skipif(sys.version_info < (3, 7), reason='Python 3.7+ required for dir support')
def test_dir():
    assert set(dir(build)) == set(build.__all__)
