from __future__ import annotations

import collections.abc
import datetime as dt
import os
import typing


__all__ = ['ConfigSettings', 'Distribution', 'JSONValue', 'StrPath', 'SubprocessRunner', 'TOMLValue']

ConfigSettings = collections.abc.Mapping[str, str | collections.abc.Sequence[str]]
Distribution = typing.Literal['sdist', 'wheel', 'editable']

StrPath = str | os.PathLike[str]

# A decoded JSON value, as produced by ``json.load``. Uses the covariant ``Sequence``/``Mapping``
# so concrete literals (e.g. ``str | list[str]``) are also assignable to it.
JSONValue: typing.TypeAlias = (
    str | int | float | bool | collections.abc.Sequence['JSONValue'] | collections.abc.Mapping[str, 'JSONValue'] | None
)

# A value as produced by ``tomllib`` when parsing ``pyproject.toml``. Uses the covariant
# ``Sequence``/``Mapping`` so concrete literals (e.g. ``dict[str, list[str]]``) are assignable.
TOMLValue: typing.TypeAlias = (
    str
    | int
    | float
    | bool
    | dt.datetime
    | dt.date
    | dt.time
    | collections.abc.Sequence['TOMLValue']
    | collections.abc.Mapping[str, 'TOMLValue']
)


class SubprocessRunner(typing.Protocol):
    """A callable that runs a build backend hook subprocess. Available as :data:`build.RunnerType`."""

    def __call__(
        self,
        cmd: collections.abc.Sequence[str],
        cwd: str | None = None,
        extra_environ: collections.abc.Mapping[str, str] | None = None,
    ) -> None:
        """
        :param cmd: The command to run
        :param cwd: The working directory
        :param extra_environ: Extra environment variables to set
        """
