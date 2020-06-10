# SPDX-License-Identifier: MIT

import sys

import casei.__main__


if __name__ == '__main__':  # pragma: no cover
    sys.argv[0] = 'python -m build'
    casei.__main__.main(sys.argv[1:])
