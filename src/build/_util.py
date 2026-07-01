from __future__ import annotations


__lazy_modules__ = [
    f'{__spec__.parent}._compat',
    'packaging',
    'packaging.requirements',
]

import re
import sys

import packaging.requirements

from ._compat import importlib


TYPE_CHECKING = False

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Set as AbstractSet


_WHEEL_FILENAME_REGEX = re.compile(
    r'(?P<distribution>.+)-(?P<version>.+)'
    r'(-(?P<build_tag>.+))?-(?P<python_tag>.+)'
    r'-(?P<abi_tag>.+)-(?P<platform_tag>.+)\.whl'
)


def check_dependency(
    req_string: str, ancestral_req_strings: tuple[str, ...] = (), parent_extras: AbstractSet[str] = frozenset()
) -> Iterator[tuple[str, ...]]:
    """
    Verify that a dependency and all of its dependencies are met.

    :param req_string: Requirement string
    :param parent_extras: Extras (eg. "test" in myproject[test])
    :yields: Unmet dependencies
    """
    yield from _check_dependency(req_string, ancestral_req_strings, parent_extras, set())


def _marker_excludes_requirement(req: packaging.requirements.Requirement, parent_extras: AbstractSet[str]) -> bool:
    """Return whether ``req``'s marker rules it out under the given parent extras."""
    if not req.marker:
        return False
    # a requirement can have multiple extras but ``evaluate`` can only check one
    # at a time; if none of them satisfy the marker the dependency is excluded.
    extras = frozenset(('',)).union(parent_extras)
    return all(not req.marker.evaluate(environment={'extra': e}) for e in extras)


def _check_dependency(
    req_string: str, ancestral_req_strings: tuple[str, ...], parent_extras: AbstractSet[str], seen: set[str]
) -> Iterator[tuple[str, ...]]:
    """
    Recursive worker for :func:`check_dependency`.

    ``seen`` memoises requirements already verified as satisfied so shared
    subtrees of a diamond dependency graph are not re-walked once per path.
    """
    req = packaging.requirements.Requirement(req_string)
    normalised_req_string = str(req)

    # ``Requirement`` doesn't implement ``__eq__`` so we cannot compare reqs for
    # equality directly but the string representation is stable.
    if normalised_req_string in ancestral_req_strings:
        # cyclical dependency, already checked.
        return

    if _marker_excludes_requirement(req, parent_extras):
        # if the marker conditions are not met, we pretend that the
        # dependency is satisfied.
        return

    # Past the marker gate the outcome depends only on ``req`` itself (name,
    # extras, specifier and installed distribution), not on ``parent_extras``,
    # so the normalised string is a sufficient memo key.
    if normalised_req_string in seen:
        return

    try:
        dist = importlib.metadata.distribution(req.name)
    except importlib.metadata.PackageNotFoundError:
        # dependency is not installed in the environment.
        yield (*ancestral_req_strings, normalised_req_string)
        return

    if req.specifier and not req.specifier.contains(dist.version, prereleases=True):
        # the installed version is incompatible.
        yield (*ancestral_req_strings, normalised_req_string)
        return

    satisfied = True
    if dist.requires:
        for other_req_string in dist.requires:
            # yields transitive dependencies that are not satisfied.
            for unmet in _check_dependency(
                other_req_string, (*ancestral_req_strings, normalised_req_string), req.extras, seen
            ):
                satisfied = False
                yield unmet

    # Only memoise fully satisfied subtrees; an unmet requirement must still be
    # reported for each dependency chain that reaches it.
    if satisfied:
        seen.add(normalised_req_string)


def format_unmet_dependencies(unmet: AbstractSet[tuple[str, ...]]) -> str:
    body = ''.join(_format_missing_dependency(chain) for chain in sorted(unmet))
    return f'Unmet dependencies (checked against {sys.executable}):{body}'


def _format_missing_dependency(dep_chain: tuple[str, ...]) -> str:
    requirement = packaging.requirements.Requirement(dep_chain[-1])
    try:
        found = importlib.metadata.distribution(requirement.name).version
    except importlib.metadata.PackageNotFoundError:
        found = 'not installed'
    wanted = str(requirement.specifier) if requirement.specifier else 'any'
    return f'\n\t{_format_dep_chain(dep_chain)}\n\t\twanted: {wanted}\n\t\tfound: {found}'


def _format_dep_chain(dep_chain: tuple[str, ...]) -> str:
    return ' -> '.join(dep.partition(';')[0].strip() for dep in dep_chain)


def parse_wheel_filename(filename: str) -> re.Match[str] | None:
    return _WHEEL_FILENAME_REGEX.match(filename)
