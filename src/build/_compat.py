import functools
import sys


if sys.version_info >= (3, 8):
    from typing import Literal, Protocol
else:
    from typing_extensions import Literal, Protocol

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
    'cache',
]
