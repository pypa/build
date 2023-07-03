import sys


if sys.version_info >= (3, 10):
    from importlib import metadata
else:
    try:
        import importlib_metadata as metadata
    except ModuleNotFoundError:
        from importlib import metadata


__all__ = ['metadata']
