from __future__ import annotations

import subprocess
import textwrap
import types


class BuildException(Exception):
    """
    Exception raised by :class:`build.ProjectBuilder`.
    """


class BuildBackendException(Exception):
    """
    Exception raised when a backend operation fails.
    """

    def __init__(
        self,
        exception: Exception,
        description: str | None = None,
        exc_info: tuple[type[BaseException], BaseException, types.TracebackType]
        | tuple[None, None, None] = (None, None, None),
    ) -> None:
        super().__init__()
        self.exception = exception
        self.exc_info = exc_info
        self._description = description

    def __str__(self) -> str:
        if self._description:
            return self._description
        return f'Backend operation failed: {self.exception!r}'


class BuildSystemTableValidationError(BuildException):
    """
    Exception raised when the ``[build-system]`` table in pyproject.toml is invalid.
    """

    def __str__(self) -> str:
        return f'Failed to validate `build-system` in pyproject.toml: {self.args[0]}'


class ProjectNameValidationError(BuildException):
    """
    Exception raised when the project name is not consistent.
    """

    def __init__(self, existing: str, existing_source: str, new: str, new_source: str) -> None:
        super().__init__()
        self._existing = existing
        self._existing_source = existing_source
        self._new = new
        self._new_source = new_source

    def __str__(self) -> str:
        return (
            f'Failed to validate project name: `{self._new}` from `{self._new_source}` '
            f'does not match `{self._existing}` from `{self._existing_source}`'
        )


class ProjectTableValidationError(BuildException):
    """
    Exception raised when the ``[project]`` table in pyproject.toml is invalid.
    """

    def __str__(self) -> str:
        return f'Failed to validate `project` in pyproject.toml: {self.args[0]}'


class FailedProcessError(Exception):
    """
    Exception raised when a setup or preparation operation fails.
    """

    def __init__(self, exception: subprocess.CalledProcessError, description: str) -> None:
        super().__init__()
        self.exception = exception
        self._description = description

    def __str__(self) -> str:
        cmd = ' '.join(self.exception.cmd)
        description = f"{self._description}\n  Command '{cmd}' failed with return code {self.exception.returncode}"
        for stream_name in ('stdout', 'stderr'):
            stream = getattr(self.exception, stream_name)
            if stream:
                description += f'\n  {stream_name}:\n'
                description += textwrap.indent(stream.decode(), '    ')
        return description


class CircularBuildDependencyError(BuildException):
    """
    Exception raised when a ``[build-system]`` requirement in pyproject.toml is circular.
    """

    def __init__(
        self, project_name: str, ancestral_req_strings: tuple[str, ...], req_string: str, backend: str | None
    ) -> None:
        super().__init__()
        self.project_name: str = project_name
        self.ancestral_req_strings: tuple[str, ...] = ancestral_req_strings
        self.req_string: str = req_string
        self.backend: str | None = backend

    def __str__(self) -> str:
        cycle_err_str = f'`{self.project_name}`'
        if self.backend:
            cycle_err_str += f' -> `{self.backend}`'
        for dep in self.ancestral_req_strings:
            cycle_err_str += f' -> `{dep}`'
        cycle_err_str += f' -> `{self.req_string}`'
        return f'Failed to validate `build-system` in pyproject.toml, dependency cycle detected: {cycle_err_str}'


class TypoWarning(Warning):
    """
    Warning raised when a possible typo is found.
    """
