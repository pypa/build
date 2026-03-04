######################
 build vs Other Tools
######################

The Python packaging ecosystem has several tools that work together. This guide helps you understand when to use build
versus other tools.

*******************
 When to use build
*******************

Use build when you want to:

- Create distribution packages (`source distributions
  <https://packaging.python.org/en/latest/specifications/source-distribution-format/>`_ and/or `wheels
  <https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_) for your project
- Build for your **current Python version and platform** only
- Create packages to upload to `PyPI <https://pypi.org/>`_
- Test that your package builds correctly
- Build as part of a development workflow

Build is a **build frontend** - it knows how to invoke :std:term:`build backends <Build Backend>` (`setuptools
<https://setuptools.pypa.io/>`_, `hatchling <https://hatch.pypa.io/latest/>`_, `flit <https://flit.pypa.io/>`_, etc.)
but doesn't handle testing, multi-version builds, or task automation.

.. code-block:: console

    $ python -m build

This builds your package for the currently active Python interpreter.

**************************
 When to use cibuildwheel
**************************

Use `cibuildwheel <https://cibuildwheel.readthedocs.io/>`_ when you need to build `wheels
<https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_ for **multiple Python versions and
platforms**:

- Building wheels for distribution on `PyPI <https://pypi.org/>`_
- Supporting Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- Supporting multiple operating systems (Linux, macOS, Windows)
- Building `manylinux <https://peps.python.org/pep-0513/>`_/`musllinux <https://peps.python.org/pep-0656/>`_ wheels
  (standardized Linux wheel formats)
- Building wheels with compiled extensions (C, C++, Rust, etc.)

cibuildwheel uses build under the hood but handles all the complexity of:

- Running builds in `manylinux containers <https://github.com/pypa/manylinux>`_
- Testing wheels after building
- Handling platform-specific quirks
- Proper `ABI tagging <https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/>`_

Example ``.github/workflows/build.yml``:

.. code-block:: yaml

    name: Build

    on: [push, pull_request]

    jobs:
      build_wheels:
        name: Build wheels on ${{ matrix.os }}
        runs-on: ${{ matrix.os }}
        strategy:
          matrix:
            os: [ubuntu-latest, windows-latest, macos-latest]

        steps:
          - uses: actions/checkout@v4
          - uses: pypa/cibuildwheel@v2.17
          - uses: actions/upload-artifact@v4
            with:
              name: wheels
              path: ./wheelhouse/*.whl

See `cibuildwheel documentation <https://cibuildwheel.readthedocs.io/>`_ for complete details.

*****************
 When to use tox
*****************

Use `tox <https://tox.wiki/>`_ when you need to:

- Test your package across multiple Python versions (e.g., 3.9, 3.10, 3.11)
- Run tests in `isolated environments <https://packaging.python.org/en/latest/glossary/#term-Virtual-Environment>`_
- Automate testing workflows
- Run linters (code checkers), formatters, type checkers
- Build documentation
- Orchestrate multiple development tasks

Example ``tox.toml``:

.. code-block:: toml

    [env_run_base]
    description = "run test suite with {basepython}"
    deps = [
        "pytest",
        "pytest-cov",
    ]
    commands = [
        ["pytest", "tests"],
    ]

    [env.build]
    description = "build the package"
    deps = ["build"]
    commands = [["python", "-m", "build"]]

    [env.lint]
    description = "run linters and type checkers"
    deps = [
        "ruff",
        "mypy",
    ]
    commands = [
        ["ruff", "check", "."],
        ["mypy", "src"],
    ]

Tox can call build to create distributions, but its main purpose is test automation.

See `tox documentation <https://tox.wiki/>`_ for complete details.

*****************
 When to use nox
*****************

Use `nox <https://nox.thea.codes/>`_ when you want tox-like functionality but prefer Python over INI:

Example ``noxfile.py``:

.. code-block:: python

    import nox


    @nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12"])
    def tests(session):
        session.install("pytest", "pytest-cov")
        session.run("pytest", "tests")


    @nox.session
    def build(session):
        session.install("build")
        session.run("python", "-m", "build")

See `nox documentation <https://nox.thea.codes/>`_ for complete details.

****************
 When to use uv
****************

Use `uv <https://docs.astral.sh/uv/>`_ when you want:

- Fast package installation (faster than pip)
- Workspace management (monorepos with multiple packages)
- Combined dependency resolution and installation
- Modern Python packaging workflows

uv can also build packages:

.. code-block:: console

    $ uv build

This is equivalent to ``python -m build --installer=uv``.

See `uv documentation <https://docs.astral.sh/uv/>`_ for complete details.

*****************
 When to use pip
*****************

Use pip when you need to:

- **Install** packages (not build them)
- Install from PyPI or other indexes
- Install in editable mode for development
- Manage dependencies in your environment

pip can build packages as a side effect of installation, but for explicit building, use build.

.. code-block:: console

    # Installing (use pip)
    $ pip install mypackage

    # Installing in editable mode (use pip)
    $ pip install -e .

    # Building distributions (use build)
    $ python -m build

************************
 How they work together
************************

A typical complete workflow might use all these tools:

Development workflow
====================

.. code-block:: console

    # Install your package in editable mode
    $ pip install -e .[dev]

    # Run tests across Python versions
    $ tox

    # Build distributions
    $ python -m build

    # Upload to PyPI
    $ twine upload dist/*

CI/CD workflow
==============

.. code-block:: yaml

    name: CI

    on: [push, pull_request]

    jobs:
      test:
        runs-on: ubuntu-latest
        strategy:
          matrix:
            python: ["3.8", "3.9", "3.10", "3.11", "3.12"]
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: ${{ matrix.python }}
          - run: pip install tox
          - run: tox -e py

      build:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: hynek/build-and-inspect-python-package@v2

      build_wheels:
        runs-on: ${{ matrix.os }}
        strategy:
          matrix:
            os: [ubuntu-latest, windows-latest, macos-latest]
        steps:
          - uses: actions/checkout@v4
          - uses: pypa/cibuildwheel@v2.17

This workflow:

1. Uses **tox** to test across Python versions
2. Uses **build** (via hynek's action) to create sdist
3. Uses **cibuildwheel** to create wheels for all platforms

***************
 Decision tree
***************

.. mermaid::

    %%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#4051b5','primaryTextColor':'#fff','primaryBorderColor':'#2c3e8f','lineColor':'#5468c4','secondaryColor':'#7c8fd6','tertiaryColor':'#e8eaf6'}}}%%
    flowchart TD
        A[What do you need to do?] --> B{Build a package?}
        B -->|Yes| C{For how many platforms?}
        B -->|No, just testing| D{Multiple Python versions?}
        B -->|No, just installing| E[Use pip or uv]

        C -->|Current platform only| F[Use python -m build]
        C -->|Multiple platforms/versions| G[Use cibuildwheel]

        D -->|Yes| H[Use tox or nox]
        D -->|No| I[Use pytest or your test runner]

        style F fill:#4051b5,stroke:#2c3e8f,color:#fff
        style G fill:#4051b5,stroke:#2c3e8f,color:#fff
        style H fill:#7c8fd6,stroke:#5468c4,color:#fff
        style I fill:#7c8fd6,stroke:#5468c4,color:#fff
        style E fill:#f57c00,stroke:#e65100,color:#fff

*****************
 Quick reference
*****************

============ ================================ ==============================
Tool         Purpose                          Use for
============ ================================ ==============================
build        Build sdist/wheel for one Python Creating distributions
cibuildwheel Build wheels for all platforms   Distributing on PyPI
tox          Test across Python versions      CI/testing automation
nox          Like tox, but Python-based       CI/testing automation
uv           Fast package manager             Installing + optional building
pip          Package installer                Installing packages
twine        Upload to PyPI                   Publishing
============ ================================ ==============================

**********
 See also
**********

- :doc:`basic-usage` for build command examples
- :doc:`ci-cd` for CI/CD integration
- :doc:`../explanation/build-backends` to understand build vs backend
