"""Handles creating a release."""

from __future__ import annotations

from pathlib import Path
from subprocess import call, check_call

from git import Commit, Remote, Repo, TagReference
from packaging.version import Version


ROOT_SRC_DIR = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT_SRC_DIR / 'src' / 'build' / '__init__.py'
CHANGELOG_FILE = ROOT_SRC_DIR / 'CHANGELOG.rst'
CHANGELOG_FRAGMENTS_DIR = ROOT_SRC_DIR / 'docs' / 'changelog'
MAJOR_FRAGMENT_TYPES = frozenset({'removal'})
MINOR_FRAGMENT_TYPES = frozenset({'feature', 'deprecation'})


def main(version_str: str, *, push: bool) -> None:
    repo = Repo(str(ROOT_SRC_DIR))
    if repo.is_dirty():
        msg = 'Current repository is dirty. Please commit any changes and try again.'
        raise RuntimeError(msg)
    remote = get_remote(repo)
    remote.fetch()
    version = resolve_version(version_str, repo)
    print(f'releasing {version}')
    release_commit = create_release_commit(repo, version)
    tag = tag_release_commit(release_commit, repo, version)
    if push:
        print('push release commit')
        repo.git.push(remote.name, 'HEAD:main')
        print('push release tag')
        repo.git.push(remote.name, tag)
    print('All done! ✨ 🍰 ✨')


def resolve_version(version_str: str, repo: Repo) -> Version:
    if version_str not in {'auto', 'major', 'minor', 'patch'}:
        return Version(version_str)
    parts = [int(x) for x in repo.git.describe('--tags', '--abbrev=0').lstrip('v').split('.')[:3]]
    match detect_bump() if version_str == 'auto' else version_str:
        case 'major':
            parts = [parts[0] + 1, 0, 0]
        case 'minor':
            parts = [parts[0], parts[1] + 1, 0]
        case 'patch':
            parts[2] += 1
    return Version('.'.join(str(p) for p in parts))


def detect_bump() -> str:
    # Semver: a removal breaks callers (major), a feature or deprecation is additive (minor), the rest is a patch.
    fragment_types = {path.suffixes[-2].lstrip('.') for path in CHANGELOG_FRAGMENTS_DIR.glob('*.*.rst')}
    if fragment_types & MAJOR_FRAGMENT_TYPES:
        return 'major'
    if fragment_types & MINOR_FRAGMENT_TYPES:
        return 'minor'
    return 'patch'


def get_remote(repo: Repo) -> Remote:
    upstream_remote = 'pypa/build'
    urls = set()
    for remote in repo.remotes:
        for url in remote.urls:
            if url.rstrip('.git').endswith(upstream_remote):
                return remote
            urls.add(url)
    msg = f'could not find {upstream_remote} remote, has {urls}'
    raise RuntimeError(msg)


def create_release_commit(repo: Repo, version: Version) -> Commit:
    print('update version in __init__.py')
    update_version_file(version)
    print('build changelog from fragments with towncrier')
    check_call(['towncrier', 'build', '--yes', '--version', version.public], cwd=str(ROOT_SRC_DIR))  # noqa: S603
    # towncrier appends the issue reference past docstrfmt's width budget, so its raw output can run over the
    # limit; reflow it here with a pinned docstrfmt instead of trusting the release job's isolated hook env,
    # which passed over-long lines into 1.5.1 and left a changelog that failed pre-commit everywhere else.
    check_call(['docstrfmt', '--line-length', '120', 'CHANGELOG.rst'], cwd=str(ROOT_SRC_DIR))
    call(['pre-commit', 'run', '--all-files'], cwd=str(ROOT_SRC_DIR))
    call(['pre-commit', 'run', '--all-files'], cwd=str(ROOT_SRC_DIR))
    repo.git.add('src/build/__init__.py', 'CHANGELOG.rst', 'docs/changelog/*')
    check_call(['pre-commit', 'run', '--all-files', '--show-diff-on-failure'], cwd=str(ROOT_SRC_DIR))
    if repo.is_dirty(index=False, working_tree=True, untracked_files=False):
        msg = 'Pre-commit hooks modified files after final run. This indicates an environment inconsistency.'
        raise RuntimeError(msg)
    return repo.index.commit(f'chore: prepare for {version}')


def update_version_file(version: Version) -> None:
    content = VERSION_FILE.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith('__version__ = '):
            lines[i] = f"__version__ = '{version}'\n"
            break
    VERSION_FILE.write_text(''.join(lines), encoding='utf-8')


def tag_release_commit(release_commit: Commit, repo: Repo, version: Version) -> TagReference:
    print('create annotated tag')
    tag_name = str(version)
    existing_tags = [x.name for x in repo.tags]
    if tag_name in existing_tags:
        print(f'delete existing tag {tag_name}')
        repo.delete_tag(repo.tags[tag_name])
    changelog_content = extract_changelog_for_version(version)
    tag_message = f'build {version}\n\n{changelog_content}'
    print(f'creating tag {tag_name}')
    repo.git.tag('-a', tag_name, '-m', tag_message, str(release_commit))
    print('✓ Created annotated tag')
    return repo.tags[tag_name]


def extract_changelog_for_version(version: Version) -> str:
    content = CHANGELOG_FILE.read_text(encoding='utf-8')
    lines = content.splitlines()
    in_version_section = False
    version_header = str(version)
    changelog_lines = []
    for line in lines:
        if version_header in line and '*' in line:
            in_version_section = True
            continue
        if in_version_section:
            if line.startswith('**') and '*' * 10 in line:
                break
            if line.strip():
                cleaned = line.replace(':pr:', 'PR #').replace(':issue:', 'issue #')
                cleaned = cleaned.replace('``', '`')
                changelog_lines.append(cleaned)
    return '\n'.join(changelog_lines).strip()


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(prog='release')
    parser.add_argument('--version', default='auto')
    parser.add_argument('--no-push', action='store_true')
    options = parser.parse_args()
    main(options.version, push=not options.no_push)
