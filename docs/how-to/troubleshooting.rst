#################
 Troubleshooting
#################

This guide helps you resolve common issues when using build.

***************************************
 Build fails with missing dependencies
***************************************

**Symptom**: Build fails with errors like "ModuleNotFoundError" or "No module named 'X'".

**Cause**: Your build backend or its dependencies aren't installed in the isolated environment.

**Solution 1**: Let build handle it automatically (default):

.. code-block:: console

    $ python -m build

Build will read your ``pyproject.toml`` and install all required dependencies.

**Solution 2**: If using ``--no-isolation``, manually install dependencies:

.. code-block:: console

    $ pip install setuptools your-build-backend
    $ python -m build --no-isolation

**********************************************
 "Unmet dependencies" with ``--no-isolation``
**********************************************

**Symptom**: A ``--no-isolation`` build stops with:

::

    ERROR Unmet dependencies (checked against /usr/local/bin/python3.9):
        anndata>=0.7.4
            wanted: >=0.7.4
            found: not installed

**Cause**: build checks the declared requirements against the interpreter named in the header (the one running build),
not against a virtual environment or your system package manager. Read each entry as:

- ``found: not installed`` - the package is invisible to *that* interpreter's metadata. If you believe it is installed
  (for example via a Linux distribution or FreeBSD port), it was installed for a different Python, so build cannot see
  it. Install it for the interpreter in the header, or run that interpreter's ``python -m build``.
- ``found: <version>`` - the package is installed but its version does not satisfy ``wanted``. Upgrade or downgrade it
  to match.

**Solution 1**: Install or fix the offending dependency for the interpreter shown in the header.

**Solution 2**: If you manage build dependencies externally (distribution packaging), skip the check entirely:

.. code-block:: console

    $ python -m build --no-isolation --skip-dependency-check

See :doc:`basic-usage` for more on ``--skip-dependency-check``.

*******************************************
 Find the backend version for a bug report
*******************************************

**Symptom**: A backend's issue tracker asks for the exact version of the backend you used. ``pyproject.toml`` lists only
the requirement specifiers (``setuptools >= 40.8.0``), and on an isolated build the resolved version lives in the
temporary environment that build deletes afterwards.

**Solution**: Read it from build's output. After installing the build dependencies, build prints the resolved version of
each one:

.. code-block:: console

    $ python -m build --wheel
    ...
    * Getting build dependencies for wheel...
    * Installed build dependency versions:
      - setuptools==82.0.1
    * Building wheel...

Copy the ``name==version`` line for the backend into your report. With ``--no-isolation`` build installs nothing, so
read the version from the active interpreter instead (for example ``pip show setuptools``).

*******************************
 Build hangs or appears frozen
*******************************

**Symptom**: Build command runs but produces no output for a long time.

**Possible causes**:

1. **Waiting for authentication**: If you're using a private package index, build may be waiting for credentials.

   See :doc:`corporate-environments` for authentication setup.

2. **Large download**: Build backend dependencies are being downloaded.

   Use ``-v`` or ``-vv`` for verbose output:

   .. code-block:: console

       $ python -m build -vv

3. **Build backend is actually running**: Some backends (especially for C extensions) can take time.

   Check system monitor for CPU/disk activity to confirm work is happening.

*************************************
 SSL certificate verification failed
*************************************

**Symptom**: Errors like "SSL: CERTIFICATE_VERIFY_FAILED" or "certificate verify failed".

**Cause**: Your system doesn't trust the SSL certificate of the package index.

**Solution 1**: Provide the CA certificate (recommended):

.. code-block:: console

    $ export PIP_CERT=/path/to/company-ca-bundle.crt
    $ python -m build

**Solution 2**: Use build with virtualenv for better SSL support:

.. code-block:: console

    $ pip install build[virtualenv]
    $ python -m build

**Solution 3**: For development only, disable verification (not recommended):

.. code-block:: console

    $ export PIP_TRUSTED_HOST=pypi.company.com
    $ python -m build

See :doc:`corporate-environments` for more details.

**************************
 Permission denied errors
**************************

**Symptom**: "PermissionError" or "Access is denied" when creating directories or files.

**Common causes**:

1. **Output directory is protected**: The ``dist/`` directory is owned by another user or process.

   Solution: Remove the directory first or use a different output location:

   .. code-block:: console

       $ rm -rf dist/
       $ python -m build

   Or:

   .. code-block:: console

       $ python -m build --outdir /tmp/my-build

2. **Running inside a read-only directory**: The source directory is on a read-only filesystem.

   Solution: Copy the source to a writable location first.

3. **Antivirus software**: Some antivirus tools block Python from creating virtual environments.

   Solution: Add Python and your project directory to antivirus exclusions.

********************************************
 Wheel is not compatible with this platform
********************************************

**Symptom**: "is not a supported wheel on this platform" when trying to install the built wheel.

**Cause**: The wheel was built for a different Python version or platform.

**Solution**: Build on the same platform and Python version where you'll install, or use cibuildwheel for multi-platform
builds.

See :doc:`choosing-tools` for when to use cibuildwheel vs build.

*********************************************
 Build succeeds but package is missing files
*********************************************

**Symptom**: After building, the package installs but is missing source files, data files, or modules.

**Cause**: Files aren't included in the source distribution manifest.

**Solution**: The fix depends on your build backend:

**For setuptools** (`setuptools documentation <https://setuptools.pypa.io/>`_):

Add a ``MANIFEST.in`` file or use ``package_data`` in ``pyproject.toml``:

.. code-block:: toml

    [tool.setuptools.package-data]
    mypackage = ["data/*.json", "templates/*.html"]

**For hatchling** (`hatchling documentation <https://hatch.pypa.io/latest/config/build/>`_):

Use the ``include`` and ``exclude`` options:

.. code-block:: toml

    [tool.hatch.build.targets.wheel]
    include = [
        "src/**/*.py",
        "src/**/*.json",
    ]

**For flit** (`flit documentation <https://flit.pypa.io/>`_):

Flit includes all files tracked by `git <https://git-scm.com/>`_ by default. Ensure files are committed.

**Test your sdist**: Always verify the sdist contains all necessary files:

.. code-block:: console

    $ python -m build --sdist
    $ tar -tzf dist/mypackage-1.0.0.tar.gz

****************************************
 ModuleNotFoundError in the built wheel
****************************************

**Symptom**: The wheel installs successfully, but importing the package fails with "ModuleNotFoundError".

**Cause**: The package structure in your source doesn't match what the build backend expects.

**Common issues**:

1. **Missing ``__init__.py``**: Ensure every package directory has an ``__init__.py`` file (not needed for namespace
   packages).
2. **Wrong directory structure**: For src-layout, ensure you have ``src/packagename/`` not just ``packagename/``.
3. **Not configuring package discovery**: Tell your build backend where to find packages.

   For setuptools with src-layout:

   .. code-block:: toml

       [tool.setuptools.packages.find]
       where = ["src"]

*********************************************
 Version conflict between build dependencies
*********************************************

**Symptom**: Build fails with errors about conflicting package versions.

**Cause**: Build dependencies have incompatible version requirements.

**Solution 1**: Update your build backend and its dependencies:

.. code-block:: console

    $ pip install --upgrade pip setuptools

Then try building again:

.. code-block:: console

    $ python -m build

**Solution 2**: If using ``--no-isolation``, create a fresh virtual environment:

.. code-block:: console

    $ python -m venv fresh-env
    $ source fresh-env/bin/activate  # On Windows: fresh-env\\Scripts\\activate
    $ pip install build
    $ python -m build

The isolated build (without ``--no-isolation``) avoids this issue by creating a clean environment each time.

*************************************
 Build works locally but fails in CI
*************************************

**Common causes**:

1. **Different Python versions**: CI may use a different Python version than your local environment.

   Solution: Specify Python version in CI config, test locally with that version.

2. **Missing system dependencies**: C extensions may need system libraries.

   Solution: Install required libraries in CI before building:

   .. code-block:: yaml

       # GitHub Actions example
       - name: Install system dependencies
         run: |
           sudo apt-get update
           sudo apt-get install -y libffi-dev

3. **File path issues**: Windows vs Unix path separators.

   Solution: Use ``pathlib.Path`` in ``pyproject.toml`` configurations and build scripts.

4. **Git not available**: Some backends use git for version detection.

   Solution: Ensure git is installed in CI, or use explicit versioning in ``pyproject.toml``.

See :doc:`ci-cd` for CI-specific guidance.

*******************************
 Catching deprecation warnings
*******************************

To catch warnings from your build backend in CI:

.. code-block:: console

    $ PYTHONWARNINGS=error::DeprecationWarning python -m build

Or for setuptools specifically:

.. code-block:: console

    $ PYTHONWARNINGS=error:::setuptools.config.setupcfg python -m build

This fails the build if deprecated features are used, helping you catch issues early.

*************************
 Build backend not found
*************************

**Symptom**: "Backend 'X' is not available" or "No module named 'X'".

**Cause**: The build backend specified in ``pyproject.toml`` isn't installed.

**Solution**: This shouldn't happen with isolated builds (the default). If you see this:

1. Check your ``pyproject.toml`` ``[build-system]`` section is correct:

   .. code-block:: toml

       [build-system]
       requires = ["hatchling"]
       build-backend = "hatchling.build"

2. If using ``--no-isolation``, install the backend:

   .. code-block:: console

       $ pip install hatchling
       $ python -m build --no-isolation

*******************************************
 No build-system section in pyproject.toml
*******************************************

**Symptom**: Build succeeds but you're not sure which backend is being used.

**Cause**: No ``[build-system]`` section is specified in ``pyproject.toml``.

**Solution**: As recommended in :PEP:`517`, if no backend is specified, build will fallback to
``setuptools.build_meta:__legacy__``. This is for backward compatibility with older projects. For new projects,
explicitly specify your build backend:

.. code-block:: toml

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

This makes your build configuration explicit and avoids relying on the fallback behavior.

***************************************
 Build installed in user site-packages
***************************************

**Symptom**: Virtual environment creation fails with errors like "executable /usr/local/bin/python missing".

**Cause**: When build is installed in the user site-packages (``pip install --user build``), it can interfere with
isolated environment creation.

**Solution**: Install build in a virtual environment instead:

.. code-block:: console

    $ python -m venv build-env
    $ source build-env/bin/activate  # On Windows: build-env\\Scripts\\activate
    $ pip install build
    $ python -m build

Or use ``pipx`` to install build in isolation:

.. code-block:: console

    $ pipx install build
    $ pipx run build

***************************************************
 Package name has dashes but wheel has underscores
***************************************************

**Symptom**: Your package is named ``my-package`` but the wheel is ``my_package-1.0.0-py3-none-any.whl``.

**This is expected behavior**: According to `PEP 427 <https://peps.python.org/pep-0427/>`_, wheel filenames normalize
package names by replacing dashes with underscores. This is not a bug.

Your users can still install with either name:

.. code-block:: console

    $ pip install my-package    # Works
    $ pip install my_package    # Also works

The package metadata preserves your original name, only the filename is normalized.

**************************
 Getting more information
**************************

Verbose output
==============

Use ``-v`` or ``-vv`` for detailed output:

.. code-block:: console

    $ python -m build -v      # Verbose
    $ python -m build -vv     # Very verbose

This shows what build is doing and can help identify where failures occur.

Check your configuration
========================

Verify your ``pyproject.toml`` is valid:

.. code-block:: console

    $ python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb')))"

Test the build backend directly
===============================

You can test if your build backend works independently:

.. code-block:: console

    $ pip install your-build-backend
    $ python -m your_build_backend

Inspect the build environment
=============================

build removes its isolated environment when the build ends. To keep it for inspection, point ``--env-dir`` at an empty
location:

.. code-block:: console

    $ python -m build --env-dir .build-env

build removes that location after a successful build and keeps it after a failure, so a failed build leaves the
environment in ``.build-env`` for you to examine. Setting ``TMPDIR`` (or ``TEMP`` on Windows) only moves the temporary
directory; it does not keep the environment around.

build forwards the backend's output to your terminal as it happens, so compilation logs and error messages are already
visible. Raise the verbosity to add build's own diagnostics and stream the environment setup live:

.. code-block:: console

    $ python -m build -vv

.. _debug-a-failed-build:

**********************
 Debug a failed build
**********************

When a backend fails, build prints a ``TIP`` line that links back here. Work through these steps to gather what you
need.

Stream the backend output
=========================

build forwards everything the backend writes to standard output and error straight to your terminal, so compiler
invocations and backend tracebacks already appear without any extra flag. Raise the verbosity to add build's own
diagnostics and to stream the environment setup (installing the backend and its dependencies) live instead of only on
failure:

.. code-block:: console

    $ python -m build -vv

Keep the build environment and sources
======================================

A failed build deletes its temporary working directories before you can look at them. Pin both so they survive the run:

.. code-block:: console

    $ python -m build --env-dir .build-env --sdist-extract-dir .build-src

``--env-dir`` keeps the isolated environment (the installed backend and its dependencies) on failure; see `Inspect the
build environment`_. ``--sdist-extract-dir`` keeps the extracted sdist, which is the directory the backend actually runs
in, so any files the backend leaves next to your sources stay put.

Find the backend's own logs
===========================

build cannot capture log *files* the backend writes inside its own working directory, because PEP 517 gives the frontend
no way to discover them. Each backend exposes its own setting for keeping them. For ``meson-python`` and
``scikit-build``, point its build directory at a path you control:

.. code-block:: console

    $ python -m build -C build-dir=_build

The backend then usually writes its build tree and logs under ``_build``. Check your backend's documentation for the
equivalent setting.

**********************
 Still having issues?
**********************

If your issue isn't covered here:

1. Check the `issue tracker <https://github.com/pypa/build/issues>`_ for similar problems
2. Enable verbose output (``-vv``) and include the full output when reporting issues
3. Include your ``pyproject.toml`` and Python version when asking for help

**********
 See also
**********

- :doc:`corporate-environments` for proxy, SSL, and authentication issues
- :doc:`ci-cd` for CI/CD-specific problems
- :doc:`../reference/environment-variables` for environment variables that affect build
