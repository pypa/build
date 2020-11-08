import abc
import sys

from typing import TYPE_CHECKING, Callable, TypeVar


_T = TypeVar('_T')


def add_metaclass(metaclass):  # type: (type) -> Callable[[_T], _T]
    """Class decorator for creating a class with a metaclass (borrowed from six code)."""

    def wrapper(cls):  # type: (_T) -> _T
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):  # pragma: no cover
                slots = [slots]  # pragma: no cover
            for slots_var in slots:  # pragma: no cover
                orig_vars.pop(slots_var)  # pragma: no cover
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        if hasattr(cls, '__qualname__'):
            orig_vars['__qualname__'] = cls.__qualname__  # type: ignore
        return metaclass(cls.__name__, cls.__bases__, orig_vars)  # type: ignore

    return wrapper


if sys.version_info[0] == 2:
    abstractproperty = abc.abstractproperty
else:
    if TYPE_CHECKING:  # pragma: no cover
        abstractproperty = property  # pragma: no cover
    else:

        def abstractproperty(func):
            return property(abc.abstractmethod(func))


__all__ = (
    'abstractproperty',
    'add_metaclass',
)
