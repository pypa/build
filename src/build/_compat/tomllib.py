from __future__ import annotations


__lazy_modules__ = ['tomli', 'tomllib']

import sys


if sys.version_info >= (3, 11):
    from tomllib import TOMLDecodeError, load, loads
else:
    from tomli import TOMLDecodeError, load, loads


__all__ = [
    'TOMLDecodeError',
    'load',
    'loads',
]
