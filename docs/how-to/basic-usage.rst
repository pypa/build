#############
 Basic Usage
#############

This guide covers the most common build commands and workflows.

********************************************************
 Building both source and wheel distributions (default)
********************************************************

By default, build creates both a `source distribution
<https://packaging.python.org/en/latest/specifications/source-distribution-format/>`_ (often called "sdist") and a
`wheel <https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_:

.. code-block:: console

    $ python -m build

This is equivalent to:

.. code-block:: console

    $ python -m build --sdist --wheel

The process:

1. Builds the source distribution from your source code
2. Extracts the source distribution to a temporary directory
3. Builds the wheel from the extracted source distribution

This two-step process ensures your source distribution contains all necessary files to build your package. If files are
missing, the wheel build will fail, alerting you to the problem.

***********************
 Building only a wheel
***********************

.. code-block:: console

    $ python -m build --wheel

Or the short form:

.. code-block:: console

    $ python -m build -w

This builds the `wheel <https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_
(installable package) directly from your source directory, skipping the source distribution step. This is faster but
doesn't verify your source distribution is complete.

*************************************
 Building only a source distribution
*************************************

.. code-block:: console

    $ python -m build --sdist

Or the short form:

.. code-block:: console

    $ python -m build -s

*********************************
 Specifying the source directory
*********************************

Build defaults to the current directory. To build from a different location:

.. code-block:: console

    $ python -m build path/to/project

Or explicitly:

.. code-block:: console

    $ python -m build --srcdir path/to/project

*********************************
 Specifying the output directory
*********************************

By default, distributions are placed in ``dist/`` within the source directory. To use a different location:

.. code-block:: console

    $ python -m build --outdir /path/to/output

Or the short form:

.. code-block:: console

    $ python -m build -o /path/to/output

***********************
 Controlling verbosity
***********************

Increase verbosity to see more details:

.. code-block:: console

    $ python -m build -v

Or even more verbose:

.. code-block:: console

    $ python -m build -vv

Decrease verbosity for quieter output:

.. code-block:: console

    $ python -m build -q

**************************
 Using a faster installer
**************************

By default, build uses `pip <https://pip.pypa.io/>`_ to install build dependencies. For faster builds, use `uv
<https://docs.astral.sh/uv/>`_ (a faster alternative to pip):

.. code-block:: console

    $ python -m build --installer=uv

This requires uv to be installed:

.. code-block:: console

    $ pip install uv

****************************
 Building without isolation
****************************

By default, build creates an `isolated environment
<https://packaging.python.org/en/latest/glossary/#term-Isolated-Build>`_ (a clean temporary `virtual environment
<https://docs.python.org/3/tutorial/venv.html>`_) to ensure reproducible builds. To skip this and use your current
environment:

.. code-block:: console

    $ python -m build --no-isolation

Or the short form:

.. code-block:: console

    $ python -m build -n

.. warning::

    When using ``--no-isolation``, you must manually install all build dependencies. This is mainly useful for:

    - Offline or air-gapped environments (no internet access)
    - Debugging build issues
    - Linux distribution packaging where dependencies are provided externally

****************************
 Skipping dependency checks
****************************

To skip checking if build dependencies are installed (requires ``--no-isolation``):

.. code-block:: console

    $ python -m build --no-isolation --skip-dependency-check

Or:

.. code-block:: console

    $ python -m build -nx

******************
 Common workflows
******************

Development build
=================

Quick build during development:

.. code-block:: console

    $ python -m build --wheel --installer=uv

Fast CI build
=============

In CI where dependencies are pre-installed:

.. code-block:: console

    $ pip install build build-backend-here
    $ python -m build --no-isolation

Release build
=============

For uploading to `PyPI <https://pypi.org/>`_, build both sdist and wheel:

.. tab:: uv

    .. code-block:: console

        $ python -m build
        $ uv publish

    `uv publish <https://docs.astral.sh/uv/guides/publish/>`_ is a modern option that handles uploading to PyPI with built-in support for trusted publishing.

.. tab:: twine

    .. code-block:: console

        $ python -m build
        $ twine check dist/*
        $ twine upload dist/*

    See the `twine documentation <https://twine.readthedocs.io/>`_ for upload options.

.. tip::

    Use the ``hynek/build-and-inspect-python-package`` GitHub Action which handles this workflow including verification.
    See :doc:`ci-cd`.

Testing the sdist
=================

Build from the sdist to ensure it's complete:

.. code-block:: console

    $ python -m build --sdist
    $ python -m build --wheel dist/mypackage-1.0.0.tar.gz

Or test installation:

.. code-block:: console

    $ python -m build
    $ python -m pip install dist/mypackage-1.0.0.tar.gz
    $ python -c "import mypackage; print(mypackage.__version__)"

***********************
 Cleaning before build
***********************

There's no built-in clean command. To ensure a fresh build, manually remove the dist directory:

.. code-block:: console

    $ rm -rf dist/
    $ python -m build

Or to avoid stale artifacts, use a unique output directory:

.. code-block:: console

    $ python -m build --outdir dist/v1.0.0

***********************************
 Getting metadata without building
***********************************

To extract package metadata without building the full package:

.. code-block:: console

    $ python -m build --metadata

This outputs the wheel metadata in JSON format to stdout.

****************************
 Checking the build version
****************************

To see which version of build you're using:

.. code-block:: console

    $ python -m build --version

************************************
 Installing build dependencies only
************************************

For specialized workflows like static analysis or linting, you may want to install just the build dependencies without
actually building:

.. code-block:: python

    from build import ProjectBuilder

    builder = ProjectBuilder(".")

    # Get all build dependencies
    requires = builder.build_system_requires
    for dist in ["sdist", "wheel"]:
        requires.extend(builder.get_requires_for_build(dist))

    # Install them
    import subprocess

    subprocess.run(["pip", "install", *requires])

This is useful when you need the same environment that build would create, but want to run other tools (like mypy, ruff,
or custom linters) instead of building the package.

See :doc:`../reference/api` for more programmatic usage examples.

**********
 See also
**********

- :doc:`config-settings` for passing options to your build backend
- :doc:`corporate-environments` for using build with private indexes
- :doc:`troubleshooting` for common problems
- :doc:`../reference/cli` for all command-line options
