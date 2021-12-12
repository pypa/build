from __future__ import annotations

import os
import re
import sys

from collections.abc import Iterator, Set

from ._exceptions import CircularBuildDependencyError

_DISTINFO_FOLDERNAME_REGEX = re.compile(r'(?P<distribution>.+)-(?P<version>.+)\.dist-info')


_SDIST_FILENAME_REGEX = re.compile(r'(?P<distribution>.+)-(?P<version>.+)\.tar.gz')


_WHEEL_FILENAME_REGEX = re.compile(
    r'(?P<distribution>.+)-(?P<version>.+)'
    r'(-(?P<build_tag>.+))?-(?P<python_tag>.+)'
    r'-(?P<abi_tag>.+)-(?P<platform_tag>.+)\.whl'
)


def project_name_from_path(basename: str, pathtype: str) -> str | None:
    match = None
    if pathtype == 'wheel':
        match = _WHEEL_FILENAME_REGEX.match(os.path.basename(basename))
    elif pathtype == 'sdist':
        match = _SDIST_FILENAME_REGEX.match(os.path.basename(basename))
    elif pathtype == 'distinfo':
        match = _DISTINFO_FOLDERNAME_REGEX.match(os.path.basename(basename))
    if match:
        return match['distribution']
    return None


def check_dependency(  # noqa: C901
    req_string: str,
    ancestral_req_strings: tuple[str, ...] = (),
    parent_extras: Set[str] = frozenset(),
    project_name: str | None = None,
    backend: str | None = None,
) -> Iterator[tuple[str, ...]]:
    """
    Verify that a dependency and all of its dependencies are met.

    :param req_string: Requirement string
    :param parent_extras: Extras (eg. "test" in myproject[test])
    :yields: Unmet dependencies
    """
    import packaging.requirements
    import packaging.utils

    if sys.version_info >= (3, 8):
        import importlib.metadata as importlib_metadata
    else:
        import importlib_metadata

    req = packaging.requirements.Requirement(req_string)
    normalised_req_string = str(req)

    # ``Requirement`` doesn't implement ``__eq__`` so we cannot compare reqs for
    # equality directly but the string representation is stable.
    if normalised_req_string in ancestral_req_strings:
        # cyclical dependency, already checked.
        return

    if req.marker:
        extras = frozenset(('',)).union(parent_extras)
        # a requirement can have multiple extras but ``evaluate`` can
        # only check one at a time.
        if all(not req.marker.evaluate(environment={'extra': e}) for e in extras):
            # if the marker conditions are not met, we pretend that the
            # dependency is satisfied.
            return

    # Front ends SHOULD check explicitly for requirement cycles, and
    # terminate the build with an informative message if one is found.
    # https://www.python.org/dev/peps/pep-0517/#build-requirements
    if project_name is not None and packaging.utils.canonicalize_name(req.name) == packaging.utils.canonicalize_name(
        project_name
    ):
        raise CircularBuildDependencyError(project_name, ancestral_req_strings, req_string, backend)

    try:
        dist = importlib_metadata.distribution(req.name)  # type: ignore[no-untyped-call]
    except importlib_metadata.PackageNotFoundError:
        # dependency is not installed in the environment.
        yield (*ancestral_req_strings, normalised_req_string)
    else:
        if req.specifier and not req.specifier.contains(dist.version, prereleases=True):
            # the installed version is incompatible.
            yield (*ancestral_req_strings, normalised_req_string)
        elif dist.requires:
            for other_req_string in dist.requires:
                # yields transitive dependencies that are not satisfied.
                yield from check_dependency(
                    other_req_string, (*ancestral_req_strings, normalised_req_string), req.extras, project_name
                )


def parse_wheel_filename(filename: str) -> re.Match[str] | None:
    return _WHEEL_FILENAME_REGEX.match(filename)
