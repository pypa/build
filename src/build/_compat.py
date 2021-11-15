import functools
import sys


if sys.version_info >= (3, 8):
    from typing import Literal, Protocol, runtime_checkable
else:
    from typing_extensions import Literal, Protocol, runtime_checkable

if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata

if sys.version_info >= (3, 9):
    cache = functools.cache

else:
    from typing import Callable, TypeVar

    _C = TypeVar('_C', bound=Callable[..., object])

    def cache(fn: _C) -> _C:
        return functools.lru_cache(maxsize=None)(fn)  # type: ignore


__all__ = [
    'Literal',
    'Protocol',
    'runtime_checkable',
    'importlib_metadata',
    'cache',
]
