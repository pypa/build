import sys


if sys.version_info < (3, 10, 2):
    try:
        import importlib_metadata as metadata
    except ModuleNotFoundError:
        # helps bootstrapping when dependencies aren't installed
        from importlib import metadata
else:
    from importlib import metadata

__all__ = ['metadata']
