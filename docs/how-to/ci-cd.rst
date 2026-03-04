###################
 CI/CD Integration
###################

This guide shows how to integrate build into your continuous integration and deployment workflows.

****************
 GitHub Actions
****************

Using hynek's build-and-inspect-python-package
==============================================

The recommended way to build and verify packages in `GitHub Actions <https://docs.github.com/en/actions>`_ is using the
`hynek/build-and-inspect-python-package <https://github.com/hynek/build-and-inspect-python-package>`_ action. This
action builds your package, inspects it for common issues, and provides the built artifacts.

.. code-block:: yaml

    name: Build

    on: [push, pull_request]

    jobs:
      build:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: hynek/build-and-inspect-python-package@v2

This action automatically:

- Builds both sdist and wheel
- Verifies the sdist contains all necessary files
- Checks for common packaging issues
- Uploads artifacts for download
- Works with any PEP 517 build backend

For more details, see the `action documentation <https://github.com/hynek/build-and-inspect-python-package>`_.

Manual build with isolation
===========================

If you need more control, use build directly with isolated environments:

.. code-block:: yaml

    name: Build

    on: [push, pull_request]

    jobs:
      build:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4

          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"

          - name: Install build
            run: pip install build

          - name: Build package
            run: python -m build

          - name: Upload artifacts
            uses: actions/upload-artifact@v4
            with:
              name: dist
              path: dist/

Fast builds with pre-installed dependencies
===========================================

For faster CI builds, pre-install build dependencies and use ``--no-isolation``:

.. code-block:: yaml

    name: Fast Build

    on: [push, pull_request]

    jobs:
      build:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4

          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"

          - name: Install dependencies
            run: |
              pip install build hatchling  # Replace hatchling with your backend

          - name: Build package
            run: python -m build --no-isolation

Using uv for faster builds
==========================

Use uv as the installer for faster dependency installation:

.. code-block:: yaml

    name: Build with uv

    on: [push, pull_request]

    jobs:
      build:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4

          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"

          - name: Install uv and build
            run: pip install uv build

          - name: Build package
            run: python -m build --installer=uv

Matrix builds across Python versions
====================================

Test building with multiple Python versions:

.. code-block:: yaml

    name: Build Matrix

    on: [push, pull_request]

    jobs:
      build:
        runs-on: ubuntu-latest
        strategy:
          matrix:
            python-version: ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]

        steps:
          - uses: actions/checkout@v4

          - uses: actions/setup-python@v5
            with:
              python-version: ${{ matrix.python-version }}

          - name: Install build
            run: pip install build

          - name: Build package
            run: python -m build

Building wheels for multiple platforms
======================================

For packages with C extensions or platform-specific code, use cibuildwheel:

.. code-block:: yaml

    name: Build Wheels

    on: [push, pull_request]

    jobs:
      build_wheels:
        name: Build wheels on ${{ matrix.os }}
        runs-on: ${{ matrix.os }}
        strategy:
          matrix:
            os: [ubuntu-latest, windows-latest, macos-13, macos-14]

        steps:
          - uses: actions/checkout@v4

          - uses: pypa/cibuildwheel@v2.17

          - uses: actions/upload-artifact@v4
            with:
              name: wheels-${{ matrix.os }}
              path: ./wheelhouse/*.whl

      build_sdist:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: hynek/build-and-inspect-python-package@v2

See :doc:`choosing-tools` for when to use build vs cibuildwheel.

Publishing to PyPI
==================

Combine building and publishing in a release workflow using the `PyPA publish action
<https://github.com/pypa/gh-action-pypi-publish>`_:

.. code-block:: yaml

    name: Publish

    on:
      release:
        types: [published]

    jobs:
      build:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: hynek/build-and-inspect-python-package@v2

      publish:
        needs: build
        runs-on: ubuntu-latest
        permissions:
          id-token: write
        steps:
          - uses: actions/download-artifact@v4
            with:
              name: Packages
              path: dist

          - uses: pypa/gh-action-pypi-publish@release/v1

***********
 GitLab CI
***********

Basic build
===========

.. code-block:: yaml

    build:
      image: python:3.12
      script:
        - pip install build
        - python -m build
      artifacts:
        paths:
          - dist/

With caching
============

Cache pip packages to speed up builds:

.. code-block:: yaml

    build:
      image: python:3.12
      cache:
        paths:
          - .cache/pip
      variables:
        PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
      script:
        - pip install build
        - python -m build
      artifacts:
        paths:
          - dist/

Fast builds with pre-installed dependencies
===========================================

.. code-block:: yaml

    build:
      image: python:3.12
      script:
        - pip install build hatchling
        - python -m build --no-isolation
      artifacts:
        paths:
          - dist/

Matrix builds
=============

.. code-block:: yaml

    .build_template:
      script:
        - pip install build
        - python -m build
      artifacts:
        paths:
          - dist/

    build:py38:
      extends: .build_template
      image: python:3.8

    build:py39:
      extends: .build_template
      image: python:3.9

    build:py312:
      extends: .build_template
      image: python:3.12

**********
 CircleCI
**********

Basic build
===========

.. code-block:: yaml

    version: 2.1

    jobs:
      build:
        docker:
          - image: cimg/python:3.12
        steps:
          - checkout
          - run:
              name: Install build
              command: pip install build
          - run:
              name: Build package
              command: python -m build
          - store_artifacts:
              path: dist/

    workflows:
      build_workflow:
        jobs:
          - build

***********
 Travis CI
***********

Basic build
===========

.. code-block:: yaml

    language: python
    python:
      - "3.8"
      - "3.9"
      - "3.10"
      - "3.11"
      - "3.12"

    install:
      - pip install build

    script:
      - python -m build

*****************
 Azure Pipelines
*****************

Basic build
===========

.. code-block:: yaml

    trigger:
      - main

    pool:
      vmImage: 'ubuntu-latest'

    strategy:
      matrix:
        Python38:
          python.version: '3.8'
        Python312:
          python.version: '3.12'

    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(python.version)'

    - script: |
        pip install build
        python -m build
      displayName: 'Build package'

    - task: PublishBuildArtifacts@1
      inputs:
        pathToPublish: 'dist'
        artifactName: 'dist'

*********
 Jenkins
*********

Declarative pipeline
====================

.. code-block:: groovy

    pipeline {
        agent any

        stages {
            stage('Build') {
                steps {
                    sh '''
                        python3 -m pip install build
                        python3 -m build
                    '''
                }
            }
            stage('Archive') {
                steps {
                    archiveArtifacts artifacts: 'dist/*', fingerprint: true
                }
            }
        }
    }

********
 Docker
********

Multi-stage build
=================

Build packages in a Docker container:

.. code-block:: dockerfile

    FROM python:3.12-slim AS builder

    WORKDIR /app

    COPY pyproject.toml README.md ./
    COPY src/ src/

    RUN pip install build && python -m build

    # Runtime image
    FROM python:3.12-slim

    COPY --from=builder /app/dist/*.whl /tmp/
    RUN pip install /tmp/*.whl && rm /tmp/*.whl

    CMD ["python"]

*****************
 tox Integration
*****************

Using build within tox environments:

.. code-block:: toml

    [env_run_base]
    description = "run test suite"
    deps = ["pytest"]
    commands = [["pytest", "tests"]]

    [env.build]
    description = "build the package"
    deps = ["build"]
    commands = [["python", "-m", "build"]]

    [env."build-check"]
    description = "build and check the package"
    deps = [
        "build",
        "twine",
    ]
    commands = [
        ["python", "-m", "build"],
        ["twine", "check", "dist/*"],
    ]

Run the build environment:

.. code-block:: console

    $ tox -e build

******************
 Verifying Builds
******************

Always verify your built packages before publishing:

.. code-block:: yaml

    - name: Check package
      run: |
        pip install twine
        twine check dist/*

Or use hynek's action which includes verification automatically.

********************
 Conditional Builds
********************

Only build on specific events:

.. code-block:: yaml

    name: Build

    on:
      push:
        branches: [main]
        tags: ['v*']
      pull_request:
        branches: [main]

    jobs:
      build:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: hynek/build-and-inspect-python-package@v2

      publish:
        if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
        needs: build
        runs-on: ubuntu-latest
        permissions:
          id-token: write
        steps:
          - uses: actions/download-artifact@v4
          - uses: pypa/gh-action-pypi-publish@release/v1

This builds on every push and PR, but only publishes when pushing a version tag.

***************************
 Troubleshooting CI Builds
***************************

Enable verbose output
=====================

Add ``-vv`` flag for debugging:

.. code-block:: yaml

    - name: Build package
      run: python -m build -vv

Preserve build artifacts
========================

Upload the dist directory even on failure:

.. code-block:: yaml

    - name: Upload artifacts
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: dist
        path: dist/

Cache build environments
========================

For repeated builds, cache pip's download cache:

.. code-block:: yaml

    - uses: actions/cache@v4
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}

**********
 See also
**********

- :doc:`troubleshooting` for build-specific issues
- :doc:`corporate-environments` for private indexes and proxies
- :doc:`choosing-tools` for when to use build vs other tools
- `hynek/build-and-inspect-python-package <https://github.com/hynek/build-and-inspect-python-package>`_ - Recommended
  GitHub Action
- `cibuildwheel <https://cibuildwheel.readthedocs.io/>`_ - For multi-platform wheel builds
