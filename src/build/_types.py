from __future__ import annotations

import os
import typing

from pyproject_hooks import SubprocessRunner as SubprocessRunner


ConfigSettings = typing.Mapping[str, typing.Union[str, typing.Sequence[str]]]
Distribution = typing.Literal['sdist', 'wheel', 'editable']
StrPath = typing.Union[str, 'os.PathLike[str]']
