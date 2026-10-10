## Description

<!-- Describe what changes you made and why -->

## Changelog

<!-- All PRs should include a changelog fragment in docs/changelog/ -->

- [ ] Added changelog fragment: `docs/changelog/<pr_number>.<type>.rst`
  - Types: `feature`, `bugfix`, `doc`, `removal`, `misc`
  - Example: `123.feature.rst` containing `` Add custom backend support - by :user:`yourname`  ``

## Checklist

- [ ] Tests pass locally (`tox`)

- [ ] Code follows project style (`tox -e fix`)

- [ ] Type checks pass (`tox -e type`)

- [ ] Documentation builds (`tox -e docs`)

- [ ] ran tests on Python 3.11 and 3.15 (`tox run -e 3.11,3.15`)

- [ ] linked upstream issues beside any temporary interpreter overrides

- [ ] kept the PR in draft until CI passes
