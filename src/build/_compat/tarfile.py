from __future__ import annotations

import sys


TYPE_CHECKING = False
if TYPE_CHECKING:
    import tarfile

# Per https://peps.python.org/pep-0706/, the "data" filter became the default
# in Python 3.14. The first series of releases with the filter had a broken
# filter that could not process symlinks correctly, so the patch releases that
# fixed it are the lower bounds here.
elif sys.version_info < (3, 10, 13) or (3, 11) <= sys.version_info < (3, 11, 5):
    from backports import tarfile  # pragma: no cover
else:  # pragma: no cover
    import tarfile


__all__ = [
    'tarfile',
]
