import os
import sys

from typing import TYPE_CHECKING, AbstractSet, Iterator, Mapping, Optional, Sequence, Tuple, Union


ConfigSettingsType = Mapping[str, Union[str, Sequence[str]]]
PathType = Union[str, 'os.PathLike[str]']

if TYPE_CHECKING:
    from typing_extensions import Literal, Protocol

    Distribution = Literal['sdist', 'wheel']
    WheelDistribution = Literal['wheel']

    class RunnerType(Protocol):
        def __call__(
            self, cmd: Sequence[str], cwd: Optional[PathType] = None, extra_environ: Optional[Mapping[str, str]] = None
        ) -> None:
            """
            Run a command in a Python subprocess.

            The parameters mirror those of ``subprocess.run``.

            :param cmd: The command to execute
            :param cwd: The working directory
            :param extra_environ: Variables to be exported to the environment
            """


def check_dependency(
    req_string: str, ancestral_req_strings: Tuple[str, ...] = (), parent_extras: AbstractSet[str] = frozenset()
) -> Iterator[Tuple[str, ...]]:
    """
    Verify that a dependency and all of its dependencies are met.

    :param req_string: Requirement string
    :param ancestral_req_strings: The dependency chain leading to this ``req_string``
    :param parent_extras: Extras (eg. "test" in ``myproject[test]``)
    :yields: Unmet dependencies
    """
    import packaging.requirements

    if sys.version_info >= (3, 8):
        import importlib.metadata as importlib_metadata
    else:
        import importlib_metadata

    req = packaging.requirements.Requirement(req_string)

    if req.marker:
        extras = frozenset(('',)).union(parent_extras)
        # a requirement can have multiple extras but ``evaluate`` can
        # only check one at a time.
        if all(not req.marker.evaluate(environment={'extra': e}) for e in extras):
            # if the marker conditions are not met, we pretend that the
            # dependency is satisfied.
            return

    try:
        dist = importlib_metadata.distribution(req.name)  # type: ignore[no-untyped-call]
    except importlib_metadata.PackageNotFoundError:
        # dependency is not installed in the environment.
        yield ancestral_req_strings + (req_string,)
    else:
        if req.specifier and not req.specifier.contains(dist.version, prereleases=True):
            # the installed version is incompatible.
            yield ancestral_req_strings + (req_string,)
        elif dist.requires:
            for other_req_string in dist.requires:
                # yields transitive dependencies that are not satisfied.
                yield from check_dependency(other_req_string, ancestral_req_strings + (req_string,), req.extras)
