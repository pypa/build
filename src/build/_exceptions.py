from __future__ import annotations


__lazy_modules__ = {f'{__spec__.parent}._util'}

from ._util import format_unmet_dependencies


TYPE_CHECKING = False

if TYPE_CHECKING:
    import subprocess


class BuildException(Exception):
    """
    Exception raised by ``build`` when a build cannot proceed.
    """


class BuildBackendException(Exception):
    """
    Exception raised when a backend operation fails.
    """

    def __init__(
        self,
        exception: Exception,
        description: str | None = None,
    ) -> None:
        super().__init__()
        self.exception: Exception = exception
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


class DependencyError(BuildException):
    """
    Exception raised when declared build dependencies are not satisfied in the current environment.
    """

    def __init__(self, unmet: set[tuple[str, ...]]) -> None:
        super().__init__()
        self.unmet: set[tuple[str, ...]] = unmet

    def __str__(self) -> str:
        return format_unmet_dependencies(self.unmet)


class FailedProcessError(Exception):
    """
    Exception raised when a setup or preparation operation fails.
    """

    def __init__(self, exception: subprocess.CalledProcessError, description: str) -> None:
        super().__init__()
        self.exception: subprocess.CalledProcessError = exception
        self._description = description

    def __str__(self) -> str:
        return self._description


class TypoWarning(Warning):
    """
    Warning raised when a possible typo is found.
    """
