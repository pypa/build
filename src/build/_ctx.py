from __future__ import annotations

import contextvars
import logging
import typing


class _Logger(typing.Protocol):  # pragma: no cover
    def __call__(self, message: str, *, origin: tuple[str, ...] | None = None) -> None:
        ...


_package_name = __spec__.parent  # type: ignore[name-defined]
_default_logger = logging.getLogger(_package_name)


def _log_default(message: str, *, origin: tuple[str, ...] | None = None) -> None:
    if origin is None:
        _default_logger.log(logging.INFO, message, stacklevel=2)


LOGGER = contextvars.ContextVar('LOGGER', default=_log_default)
VERBOSITY = contextvars.ContextVar('VERBOSITY', default=0)


if typing.TYPE_CHECKING:
    log: _Logger
    verbosity: bool

else:

    def __getattr__(name):
        if name == 'log':
            return LOGGER.get()
        elif name == 'verbosity':
            return VERBOSITY.get()
        raise AttributeError(name)  # pragma: no cover


__all__ = [
    'log',
    'LOGGER',
    'verbosity',
    'VERBOSITY',
]
