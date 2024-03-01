# SPDX-License-Identifier: MIT

import build


def test_version():
    assert build.__version__


def test_dir():
    assert set(dir(build)) == set(build.__all__)
