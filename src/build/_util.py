from __future__ import annotations

import re


TYPE_CHECKING = False

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Set as AbstractSet

    from ._compat.importlib import metadata


_WHEEL_FILENAME_REGEX = re.compile(
    r'(?P<distribution>.+)-(?P<version>.+)'
    r'(-(?P<build_tag>.+))?-(?P<python_tag>.+)'
    r'-(?P<abi_tag>.+)-(?P<platform_tag>.+)\.whl'
)


def _url_matches_direct_url(req_url: str, dist: metadata.Distribution) -> bool:
    """Check if the installed distribution's origin (PEP 610) matches the requirement URL."""
    import json

    if not (raw := dist.read_text('direct_url.json')):
        return False
    direct_url: dict[str, object] = json.loads(raw)
    url = direct_url.get('url', '')
    if isinstance(vcs_info := direct_url.get('vcs_info'), dict):
        origin = f'{vcs_info.get("vcs", "")}+{url}'
        if requested_revision := vcs_info.get('requested_revision'):
            origin += f'@{requested_revision}'
        return bool(req_url == origin)
    return bool(req_url == url)


def check_dependency(
    req_string: str, ancestral_req_strings: tuple[str, ...] = (), parent_extras: AbstractSet[str] = frozenset()
) -> Iterator[tuple[str, ...]]:
    """
    Verify that a dependency and all of its dependencies are met.

    :param req_string: Requirement string
    :param parent_extras: Extras (eg. "test" in myproject[test])
    :yields: Unmet dependencies
    """
    import packaging.requirements

    from ._compat import importlib

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

    try:
        dist = importlib.metadata.distribution(req.name)
    except importlib.metadata.PackageNotFoundError:
        # dependency is not installed in the environment.
        yield (*ancestral_req_strings, normalised_req_string)
    else:
        if req.url and not _url_matches_direct_url(req.url, dist):
            # the installed distribution's origin does not match the URL requirement (PEP 610).
            yield (*ancestral_req_strings, normalised_req_string)
        elif req.specifier and not req.specifier.contains(dist.version, prereleases=True):
            # the installed version is incompatible.
            yield (*ancestral_req_strings, normalised_req_string)
        elif dist.requires:
            for other_req_string in dist.requires:
                # yields transitive dependencies that are not satisfied.
                yield from check_dependency(other_req_string, (*ancestral_req_strings, normalised_req_string), req.extras)


def parse_wheel_filename(filename: str) -> re.Match[str] | None:
    return _WHEEL_FILENAME_REGEX.match(filename)
