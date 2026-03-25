"""Handles creating a release."""

from __future__ import annotations

from pathlib import Path
from subprocess import call, check_call

from git import Commit, Remote, Repo, TagReference
from packaging.version import Version


ROOT_SRC_DIR = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT_SRC_DIR / 'src' / 'build' / '__init__.py'
CHANGELOG_FILE = ROOT_SRC_DIR / 'CHANGELOG.rst'


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
    latest_tag = repo.git.describe('--tags', '--abbrev=0')
    latest_tag = latest_tag.lstrip('v')
    parts = [int(x) for x in latest_tag.split('.')]
    if version_str == 'major':
        parts = [parts[0] + 1, 0, 0]
    elif version_str == 'minor':
        parts = [parts[0], parts[1] + 1, 0]
    elif version_str == 'patch':
        parts[2] += 1
    elif version_str == 'auto':
        parts[2] += 1
    return Version('.'.join(str(p) for p in parts))


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
    check_call(['towncrier', 'build', '--yes', '--version', version.public], cwd=str(ROOT_SRC_DIR))
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
        repo.delete_tag(tag_name)
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
