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

    $ pip install setuptools wheel your-build-backend
    $ python -m build --no-isolation

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

    $ pip install --upgrade pip setuptools wheel

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

Preserve build logs and temporary directories
=============================================

By default, build cleans up the temporary build directory after completion. To keep it for debugging:

.. code-block:: console

    $ TMPDIR=/tmp/debug-build python -m build

The build will create its temporary environment in ``/tmp/debug-build`` and you can inspect it after the build completes
or fails. On Windows, use ``TEMP`` instead of ``TMPDIR``:

.. code-block:: console

    $ set TEMP=C:\debug-build
    $ python -m build

To see backend logs in real-time, use verbose output:

.. code-block:: console

    $ python -m build -vv

This shows all output from the build backend, including compilation logs for C extensions and detailed error messages.

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
