# build

[![CI check](https://github.com/pypa/build/workflows/check/badge.svg)](https://github.com/pypa/build/actions)
[![CI test](https://github.com/pypa/build/actions/workflows/test.yml/badge.svg)](https://github.com/pypa/build/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/pypa/build/branch/main/graph/badge.svg)](https://codecov.io/gh/pypa/build)
[![Documentation Status](https://readthedocs.org/projects/pypa-build/badge/?version=latest)](https://pypa-build.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/build.svg)](https://pypi.org/project/build/)
[![Discord](https://img.shields.io/discord/803025117553754132?label=Discord%20chat%20%23build&style=flat-square)](https://discord.gg/pypa)

A simple, correct PEP517 package builder.

See the [documentation](https://pypa-build.readthedocs.io/en/latest/) for more information.

### Installation

`build` can be installed via `pip` or an equivalent via:

```console
$ pip install build
```

### Usage

```console
$ python -m build
```

This will build the package in an isolated environment, generating a
source-distribution and wheel in the directory `dist/`.
See the [documentation](https://pypa-build.readthedocs.io/en/latest/) for full information.

### Code of Conduct

Everyone interacting in the build's codebase, issue trackers, chat rooms, and mailing lists is expected to follow
the [PSF Code of Conduct].

[psf code of conduct]: https://github.com/pypa/.github/blob/main/CODE_OF_CONDUCT.md
