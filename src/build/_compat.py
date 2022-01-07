import functools
import sys

from typing import TYPE_CHECKING


class _GenericGetitemMeta(type):
    # ``__class_getitem__`` was added in 3.7.
    # TODO: Merge into ``_GenericGetitem`` when we drop support for Python 3.6.
    def __getitem__(self, value: object) -> None:
        ...


class _GenericGetitem(metaclass=_GenericGetitemMeta):
    pass


if sys.version_info >= (3, 8):
    from typing import Literal, Protocol
else:
    if TYPE_CHECKING:
        from typing_extensions import Literal, Protocol
    else:
        from abc import ABC as Protocol

        Literal = _GenericGetitem


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
    'importlib_metadata',
    'cache',
]
