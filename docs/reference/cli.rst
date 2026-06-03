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

*************************
 Machine-Readable Output
*************************

A distribution's filename depends on its version, Python tag and platform, which the build backend settles at build
time. ``--json-output`` writes the resulting filenames to a file, or to standard output with ``-``, so a script can read
them without globbing ``dist/`` or parsing human output:

.. code-block:: console

    $ python -m build --json-output report.json
    $ python -m build --json-output -

Report format
=============

The report is a single JSON object. A default ``python -m build`` run, which builds an sdist and then a wheel from it,
produces:

.. code-block:: json

    {
      "version": 1,
      "artifacts": [
        {"distribution": "sdist", "name": "pkg-1.0.tar.gz", "path": "/home/me/pkg/dist/pkg-1.0.tar.gz"},
        {"distribution": "wheel", "name": "pkg-1.0-py3-none-any.whl", "path": "/home/me/pkg/dist/pkg-1.0-py3-none-any.whl"}
      ]
    }

The top-level object has these fields:

``version`` (integer)
    Schema version of the report, so a consumer can guard against a layout it does not understand. The current value is
    ``1``; a backward-incompatible change to the format will raise it.

``artifacts`` (array of objects)
    One entry per distribution build produced, in the order build built them. A ``--sdist``-only run lists a single
    sdist; ``--wheel`` lists a single wheel; the default run lists the sdist followed by the wheel. A run that builds
    nothing leaves this empty (``[]``).

Each entry in ``artifacts`` has these fields:

``distribution`` (string)
    The kind of distribution: ``"sdist"`` for a source distribution or ``"wheel"`` for a wheel.

``name`` (string)
    The bare filename the backend produced, for example ``pkg-1.0-cp312-cp312-manylinux_2_17_x86_64.whl``. It is the
    basename of ``path``.

``path`` (string)
    The absolute path to the file, under ``--outdir`` (``dist/`` by default). Hand this straight to an installer or
    uploader.

For example, to upload every artifact, or to install only the wheel:

.. code-block:: console

    $ twine upload $(jq -r '.artifacts[].path' report.json)
    $ pip install "$(jq -r '.artifacts[] | select(.distribution == "wheel") | .path' report.json)"

With ``-``, build sends the ``Successfully built`` summary to standard error and leaves the JSON document alone on
standard output. You cannot combine ``--json-output`` with ``--metadata``.

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
