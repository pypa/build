##############
 How it Works
##############

This document explains how build works internally and the build process flow.

*******************
 The Build Process
*******************

When you run ``python -m build``, the following happens:

.. mermaid::

    %%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#4051b5','primaryTextColor':'#fff','primaryBorderColor':'#2c3e8f','lineColor':'#5468c4','secondaryColor':'#7c8fd6','tertiaryColor':'#e8eaf6'}}}%%
    flowchart TD
        A[Run python -m build] --> B[Read pyproject.toml]
        B --> C{Isolated build?}
        C -->|Yes default| D[Create temporary venv]
        C -->|--no-isolation| E[Use current environment]
        D --> F[Install build dependencies]
        E --> F
        F --> G[Invoke build backend hooks]
        G --> H{Build what?}
        H -->|Default| I[Build sdist]
        I --> J[Extract sdist to temp dir]
        J --> K[Build wheel from sdist]
        H -->|--sdist| L[Build sdist only]
        H -->|--wheel| M[Build wheel from source]
        K --> N[Output to dist/]
        L --> N
        M --> N
        N --> O[Cleanup temporary environment]
        O --> P[Done]

        style A fill:#4051b5,stroke:#2c3e8f,color:#fff
        style P fill:#2e7d32,stroke:#1b5e20,color:#fff
        style N fill:#f57c00,stroke:#e65100,color:#fff
        style D fill:#7c8fd6,stroke:#5468c4,color:#fff
        style G fill:#7c8fd6,stroke:#5468c4,color:#fff

The process in detail:

1. **Read pyproject.toml**

   build reads your project's `pyproject.toml <https://packaging.python.org/en/latest/specifications/pyproject-toml/>`_
   to determine:

   - Which **build backend** to use (from ``[build-system]`` section)
   - What dependencies the backend needs (``requires`` list)
   - Build backend configuration (``backend-path`` if specified)

2. **Create isolated environment** (default behavior)

   build creates a temporary `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ to ensure
   reproducible builds:

   - Creates a fresh virtualenv in a temporary directory
   - Sets ``VIRTUAL_ENV`` `environment variable <https://docs.python.org/3/library/venv.html#how-venvs-work>`_
   - Installs the build backend and its dependencies via `pip <https://pip.pypa.io/>`_

   This isolation ensures your build doesn't depend on what's installed in your development environment, making builds
   reproducible across different machines.

3. **Invoke build backend hooks**

   build calls standardized hooks (functions) in your **build backend**:

   - For source distributions: calls ``build_sdist(sdist_directory, config_settings=None)``
   - For wheels: calls ``build_wheel(wheel_directory, config_settings=None, metadata_directory=None)``

   These hooks are defined in :PEP:`517` (the build system interface standard).

   build runs each hook in a subprocess and forwards its standard output and error straight through, so a failing
   backend's messages reach your terminal regardless of verbosity (``-vv`` adds build's own diagnostics on top). build
   cannot collect log *files* the backend writes inside its own working directory: :PEP:`517` exposes no way for a
   frontend to learn where those live, so retrieving them depends on backend-specific settings. See
   :ref:`debug-a-failed-build` for how to keep them.

4. **Build artifacts**

   The backend creates `distribution files
   <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_:

   - **Source distribution (sdist)**: A `tarball
     <https://packaging.python.org/en/latest/specifications/source-distribution-format/>`_ (``package-version.tar.gz``)
     containing your source code
   - **Wheel**: A `zip file <https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_
     (``package-version-py3-none-any.whl``) that can be installed directly

5. **Cleanup**

   build removes the temporary isolated environment, leaving only the distribution files in ``dist/``.

************************
 Default Build Strategy
************************

By default, ``python -m build`` creates both sdist and wheel following this strategy:

1. Build sdist from source directory
2. Extract sdist to temporary directory
3. Build wheel from the extracted sdist

This "build wheel from sdist" strategy ensures your sdist is complete. If files are missing from the sdist, the wheel
build will fail, alerting you to the problem.

Step 2 defaults to a random temporary directory that build removes after the run. Build randomises the path on purpose:
it surfaces backends that hard-code absolute paths and keeps successive builds independent. That same randomness defeats
compiler caches keyed on the source path, so ``--sdist-extract-dir`` lets you opt into a stable, persistent location
when cache hits matter more than isolation.

If the positional argument is a ``.tar.gz`` rather than a directory, the default is **wheel-only**: build checks the
archive, extracts it into a temporary directory, and runs the wheel build against the extracted source. There is no
sdist step. The archive already is an sdist, and PEP 517 has no hook for turning one sdist into another, so ``--sdist``
against an sdist errors out.

***************************
 Build Isolation Explained
***************************

Why isolation matters
=====================

Without isolation, builds can be non-reproducible. Different developers have different packages installed, and CI
environments may have different packages than local development. Upgrading a package in your dev environment could break
builds, and you might accidentally depend on a package that's not declared. Isolation solves this by creating a clean
environment for every build.

How isolation works
===================

1. build creates a temporary virtual environment using Python's ``venv`` module
2. Installs only the packages listed in ``[build-system] requires``
3. Runs the build backend in this isolated environment
4. Deletes the environment after building

The isolated environment has access to the Python standard library, the build backend and its dependencies, and nothing
from your development environment except environment variables.

build picks a temporary directory for this environment by default and deletes it after the build. Pass ``--env-dir`` to
choose the location yourself. You might do this to keep a failed environment for inspection, to place the environment on
a writable path inside a read-only container, or to give a fixed path to a compilation cache such as ccache or sccache.
Those caches treat a changed build-environment path as a new file, so a path that changes every run never hits the
cache.

When to disable isolation
=========================

Use ``--no-isolation`` only when:

- You're in an offline/air-gapped environment and have pre-installed dependencies
- You're debugging build issues and need to inspect the environment
- You're a Linux distribution packager providing dependencies externally
- You understand the reproducibility implications

Under ``--no-isolation`` build installs nothing; it instead validates that the declared dependencies are already present
(use ``--skip-dependency-check`` to opt out), so a missing dependency is reported rather than silently producing a
broken build. That check compares each declared requirement against the installed metadata of the *single interpreter
running build*, discovered through ``importlib.metadata``. This explains two otherwise confusing outcomes, which the
error message spells out per requirement (``wanted`` versus ``found``). A package can be present but reported missing
because its installed version does not satisfy the specifier (``found`` shows that version). And a package you know is
installed can read as ``not installed`` when it was installed for a *different* Python — a system or distribution
package manager often targets an interpreter other than the one invoking build, and metadata is not shared across
interpreters. The error names the interpreter checked so the mismatch is visible rather than left to guesswork.

See :doc:`../how-to/basic-usage` for usage.

***********************************
 Build Frontends vs Build Backends
***********************************

build is a **build frontend** that reads ``pyproject.toml``, creates isolated environments, invokes build backends, and
handles the command-line interface. It does NOT know how to build your specific package.

Your **build backend** (setuptools, hatchling, flit, etc.) knows how to build your package by implementing PEP 517
hooks. The backend handles package discovery, file inclusion, metadata generation, and creates the actual sdist and
wheel files.

This separation of concerns allows different backends for different project needs, ensures frontend improvements benefit
all backends, and allows backend improvements to work with all frontends.

See :doc:`build-backends` for more details.

*********************
 PEP 517 Integration
*********************

build implements :PEP:`517` (the standardized build system interface that defines how build tools communicate with
backends). The key concepts:

Build system table
==================

Your `pyproject.toml <https://packaging.python.org/en/latest/specifications/pyproject-toml/>`_ must have a
``[build-system]`` section:

.. code-block:: toml

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

- ``requires``: Packages needed to build (installed in isolated environment)
- ``build-backend``: Python import path to backend object

Backend hooks
=============

build calls these standardized hooks in your backend:

- ``get_requires_for_build_sdist(config_settings)`` - Returns additional dependencies needed for sdist
- ``build_sdist(sdist_directory, config_settings)`` - Creates sdist, returns filename
- ``get_requires_for_build_wheel(config_settings)`` - Returns additional dependencies needed for wheel
- ``build_wheel(wheel_directory, config_settings, metadata_directory)`` - Creates wheel, returns filename

Optional hooks:

- ``prepare_metadata_for_build_wheel(metadata_directory, config_settings)`` - Generates wheel metadata without full
  build

Config settings
===============

The ``config_settings`` parameter in hooks receives settings from ``--config-setting`` / ``-C`` flags.

build converts:

.. code-block:: console

    $ python -m build -C key=value

Into:

.. code-block:: python

    config_settings = {"key": "value"}

The backend interprets these settings. See :doc:`../how-to/config-settings` for examples.

*********************
 Metadata Extraction
*********************

build can extract package metadata without a full build:

.. code-block:: console

    $ python -m build --metadata

This:

1. Creates isolated environment
2. Calls ``prepare_metadata_for_build_wheel()`` if available
3. Otherwise, calls ``build_wheel()`` and extracts metadata
4. Outputs metadata in JSON format to stdout

Useful for tools that need package metadata without building the full package.

***************************
 Diagnostics and Verbosity
***************************

``pyproject.toml`` declares build dependencies as *specifiers* (``setuptools >= 40.8.0``), not exact versions. The
installer resolves each specifier to a concrete version at build time, and on an isolated build that version lives only
in the temporary environment, which build deletes once it finishes. The installer's own output reports the versions, but
only at ``-vv``, interleaved with the rest of its log.

So once build has installed the dependencies it prints a concise summary of the resolved version of each, as
``name==version``, the single piece a backend bug report usually asks for. build obtains these by reading the installed
distribution metadata from the environment's ``site-packages`` through ``importlib.metadata`` rather than by spawning a
process inside the environment, so the summary is cheap and works the same for the ``venv``/``virtualenv`` and ``uv``
backends. Because it reads installed metadata, it reflects what build used, including any transitive resolution the
specifier allowed.

This is an isolated-build concern. Under ``--no-isolation`` build installs nothing - it builds against the interpreter
that is already running it - so the versions are whatever that interpreter has, discoverable with your installer.

****************
 Error Handling
****************

build performs minimal error handling:

- Validates ``pyproject.toml`` exists and is valid TOML
- Checks ``[build-system]`` section exists
- Verifies backend is importable
- Checks hook return values are valid

Most error handling is delegated to the backend. If the backend fails, build reports the error and exits.

This keeps build simple and focused on its role as a frontend.

*********************
 Installer Selection
*********************

By default, build uses pip to install dependencies in isolated environments. You can use a different installer:

.. code-block:: console

    $ python -m build --installer=uv

Requirements for custom installers:

- Must accept ``install`` command
- Must accept package specifications as arguments
- Must support ``--no-deps`` flag

Currently, pip and uv are the primary supported installers.

*****************************
 Virtual Environment Backend
*****************************

build can use different virtual environment implementations:

- ``venv`` (default): Python's built-in venv module
- ``virtualenv``: Third-party virtualenv package

To use virtualenv:

.. code-block:: console

    $ pip install build[virtualenv]
    $ python -m build

virtualenv provides better SSL support on older Python versions, faster environment creation, and more features (though
build uses only basic functionality).

See :doc:`../how-to/corporate-environments` for when this matters.

****************************
 Output Directory Structure
****************************

By default, build places files in ``dist/`` within your source directory:

.. code-block:: text

    myproject/
    ├── dist/
    │   ├── myproject-1.0.0.tar.gz      # sdist
    │   └── myproject-1.0.0-py3-none-any.whl  # wheel
    ├── src/
    │   └── myproject/
    │       └── __init__.py
    └── pyproject.toml

Use ``--outdir`` to change the output location:

.. code-block:: console

    $ python -m build --outdir /tmp/build-output

*******************************
 Environment Variable Handling
*******************************

build passes most environment variables to the build backend:

**Always passed**:

- ``PATH`` - For finding executables
- ``PYTHONPATH`` - For Python module discovery
- HTTP/HTTPS proxy variables
- SSL certificate variables
- Custom pip variables (``PIP_*``)

**Set by build**:

- ``VIRTUAL_ENV`` - Points to isolated environment (when using isolation)

**When using ``--no-isolation``**:

- All environment variables from your shell are passed through unchanged

This behavior allows corporate environments to configure pip via environment variables, build backends to use custom
environment variables, and proxy and SSL configuration to work transparently.

See :doc:`../reference/environment-variables` for details.

*********************
 Reproducible Builds
*********************

build aims for reproducible builds by:

1. **Isolated environments**: Same dependencies every time
2. **Declared dependencies**: ``[build-system] requires`` is explicit
3. **Standardized interface**: PEP 517 hooks are well-defined
4. **Minimal intervention**: build doesn't modify your code or backend behavior

However, full reproducibility also requires pinned backend versions in ``requires``, reproducible builds in your backend
(some backends support ``SOURCE_DATE_EPOCH``), consistent Python version, and consistent platform for platform-specific
wheels.

***************
 Build Reports
***************

The names of the distribution files build produces are not known ahead of time. They encode the version and, for wheels,
the Python, ABI and platform tags. Downstream steps such as uploading, signing, or recording checksums need a way to
learn what was built.

``--report`` writes this information to a JSON file. It uses a file rather than ``stdout`` because the build backend
runs as a subprocess that inherits build's streams and may print to them, so a consumer could not separate the report
from backend chatter on ``stdout``. A file build controls keeps the machine-readable output apart from the human- and
backend-facing log. Build writes the report only after the build succeeds and replaces it atomically, so a consumer
never reads a half-written file. See :doc:`../reference/cli` for the schema.

****************************
 Performance Considerations
****************************

Build time is dominated by:

1. **Environment creation**: Creating virtualenv (1-2 seconds)
2. **Dependency installation**: Installing backend and dependencies (varies)
3. **Backend build**: Actual package building (varies greatly)

Ways to speed up builds include using ``--installer=uv`` for faster dependency installation, using ``--no-isolation`` if
dependencies are pre-installed (loses reproducibility), installing ``build[virtualenv]`` for faster environment
creation, and using ``--wheel`` to skip sdist when not needed.

The default (isolation with pip) prioritizes reproducibility over speed.

**********
 See also
**********

- :doc:`build-backends` for choosing and configuring backends
- `PEP 517 <https://peps.python.org/pep-0517/>`_ for the build system specification
- `PEP 518 <https://peps.python.org/pep-0518/>`_ for the ``pyproject.toml`` specification
