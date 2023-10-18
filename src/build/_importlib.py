import sys


if sys.version_info >= (3, 10, 2):
    from importlib import metadata  # type: ignore[attr-defined]
else:
    try:
        import importlib_metadata as metadata
    except ModuleNotFoundError:
        # helps bootstrapping when dependencies aren't installed
        from importlib import metadata  # type: ignore[attr-defined]

__all__ = ['metadata']
