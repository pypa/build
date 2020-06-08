# SPDX-License-Identifier: MIT

import os
import sys


f = os.readlink(__file__) if os.path.islink(__file__) else __file__
path = os.path.realpath(os.path.join(f, '..', '..'))

if path not in sys.path:  # pragma: no cover
    sys.path.insert(0, path)
