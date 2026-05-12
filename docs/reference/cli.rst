########################
 Command-Line Interface
########################

A simple, correct Python build frontend.

By default, a `source distribution (sdist)
<https://packaging.python.org/en/latest/specifications/source-distribution-format/>`_ is built from the project root and
a `binary distribution (wheel) <https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_ is
built from the sdist. If this is undesirable, you can pass ``--sdist`` and/or ``--wheel`` to build distributions
independently of each other.

The positional ``srcdir`` argument also accepts a ``.tar.gz`` source distribution. Build checks the filename and the
presence of ``PKG-INFO``, extracts the archive into a temporary directory, and runs the wheel build against the
extracted source. The default ``--outdir`` is the directory containing the archive. ``--sdist`` errors against an
archive, since the archive already is an sdist.

.. sphinx_argparse_cli::
    :module: build.__main__
    :func: main_parser
    :prog: python -m build
    :title: python -m build
    :usage_width: 97

********************
 Isolation Behavior
********************

By default build will build the package in an isolated environment, but this behavior can be disabled with
``--no-isolation``. When using isolation, build creates a temporary virtual environment, installs the build dependencies
specified in your ``pyproject.toml``, runs the build, and then cleans up the environment. This ensures reproducible
builds regardless of what packages are installed in your development environment.

************************
 Alternative CLI Script
************************

A ``pyproject-build`` CLI script is also available, which is functionally identical to ``python -m build``. This is
useful for tools like pipx_ that prefer direct script entry points.

.. code-block:: console

    $ pyproject-build
    $ pyproject-build --help

Both commands accept the same options and behave identically.

*****************
 Common Patterns
*****************

For practical usage examples and workflows, see :doc:`../how-to/basic-usage`.

**********
 See Also
**********

- :doc:`../how-to/basic-usage` for common workflows
- :doc:`../how-to/config-settings` for passing options to backends
- :doc:`environment-variables` for environment variables that affect build

.. _pipx: https://github.com/pipxproject/pipx
