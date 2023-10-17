import sys


if sys.version_info < (3, 10, 2):
    import importlib_metadata as metadata
else:
    from importlib import metadata

__all__ = ['metadata']
