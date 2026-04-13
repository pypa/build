from __future__ import annotations

import os
import typing


__all__ = ['ConfigSettings', 'Distribution', 'StrPath', 'SubprocessRunner']

ConfigSettings = typing.Mapping[str, str | typing.Sequence[str]]
Distribution = typing.Literal['sdist', 'wheel', 'editable']

StrPath = str | os.PathLike[str]

TYPE_CHECKING = False

if TYPE_CHECKING:
    from pyproject_hooks import SubprocessRunner
else:
    SubprocessRunner = typing.Callable[[typing.Sequence[str], str | None, typing.Mapping[str, str] | None], None]
