from __future__ import annotations


TYPE_CHECKING = False

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Set as AbstractSet


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
        if req.specifier and not req.specifier.contains(dist.version, prereleases=True):
            # the installed version is incompatible.
            yield (*ancestral_req_strings, normalised_req_string)
        elif dist.requires:
            for other_req_string in dist.requires:
                # yields transitive dependencies that are not satisfied.
                yield from check_dependency(other_req_string, (*ancestral_req_strings, normalised_req_string), req.extras)


def parse_wheel_filename(filename: str) -> dict[str, str] | None:
    from packaging.utils import InvalidWheelFilename
    from packaging.utils import parse_wheel_filename as validate_wheel_filename

    try:
        validate_wheel_filename(filename)
    except InvalidWheelFilename:
        return None

    filename_without_extension = filename.removesuffix('.whl')
    parts = filename_without_extension.split('-')
    if len(parts) == 5:
        distribution, version, python_tag, abi_tag, platform_tag = parts
        build_tag = None
    else:
        distribution, version, build_tag, python_tag, abi_tag, platform_tag = parts

    result = {
        'distribution': distribution,
        'version': version,
        'python_tag': python_tag,
        'abi_tag': abi_tag,
        'platform_tag': platform_tag,
    }
    if build_tag:
        result['build_tag'] = build_tag
    return result
