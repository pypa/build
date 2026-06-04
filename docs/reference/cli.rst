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

Pass ``--env-dir PATH`` to put the environment at a fixed location instead of a temporary directory. The location must
be empty. build removes it after a successful build and keeps it after a failure so you can inspect it. A fixed path
helps compilation caches like ccache and sccache, which treat a changed build-environment path as a new file and miss
the cache. You cannot combine ``--env-dir`` with ``--no-isolation``.

******************
 Dependency Check
******************

With ``--no-isolation``, build does not install anything; it checks that the build dependencies are already present in
the interpreter running build. When a requirement is unmet it exits with an ``Unmet dependencies`` error that names the
interpreter checked and, for each requirement, the version specifier that was ``wanted`` and the version that was
``found`` (``not installed`` when absent):

.. code-block:: text

    ERROR Unmet dependencies (checked against /usr/local/bin/python3.9):
        anndata>=0.7.4
            wanted: >=0.7.4
            found: not installed
        matplotlib>=3.4 -> kiwisolver>=1.0.1
            wanted: >=1.0.1
            found: 1.0.0

Transitive requirements are shown as a ``parent -> child`` chain; the ``wanted``/``found`` lines describe the unmet
leaf. Pass ``--skip-dependency-check`` to skip this check (see :doc:`../how-to/basic-usage`).

****************
 Verbose Output
****************

Repeating ``-v`` raises the verbosity level. Each level adds to the previous one:

- ``-v`` streams the output of the environment-creation and dependency-installation subprocesses.
- ``-vv`` additionally passes ``-v`` through to the installer.

Regardless of verbosity, after installing the build dependencies of an isolated build, build prints a summary of the
resolved versions, one ``name==version`` per line. build reads these from the isolated environment's installed metadata,
so they reflect what was installed rather than the specifiers in ``pyproject.toml``:

.. code-block:: console

    $ python -m build --wheel
    * Creating isolated environment: venv+pip...
    * Installing packages in isolated environment:
      - setuptools >= 42.0.0
    * Getting build dependencies for wheel...
    * Installed build dependency versions:
      - setuptools==82.0.1
    * Building wheel...
    Successfully built mypackage-1.0.0-py3-none-any.whl

build reports this for isolated builds only; with ``--no-isolation`` build installs nothing, so inspect the active
interpreter with your installer instead (for example ``pip list``).

**************
 Build Report
**************

``--report PATH`` writes a JSON description of the built artifacts to ``PATH`` after a successful build. The artifact
names are dynamic (they encode version, Python, ABI and platform tags), so this gives scripts and CI a stable way to
refer to the produced files instead of globbing ``dist/``. Build writes the report to a file it controls, not to
standard output, because the build backend may write to ``stdout``/``stderr`` too. The report is JSON.

.. code-block:: console

    $ python -m build --report dist/report.json
    $ twine upload $(jq -r '.artifacts[].path' dist/report.json)

The schema is:

.. code-block:: json

    {
      "version": "1.0",
      "artifacts": [
        {
          "name": "mypackage-0.1.0.tar.gz",
          "path": "dist/mypackage-0.1.0.tar.gz",
          "kind": "sdist",
          "size": 4096,
          "hashes": {"sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
        },
        {
          "name": "mypackage-0.1.0-py3-none-any.whl",
          "path": "dist/mypackage-0.1.0-py3-none-any.whl",
          "kind": "wheel",
          "size": 2048,
          "hashes": {"sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
        }
      ]
    }

``version`` is the schema version. Each artifact lists its ``name`` (basename), ``path`` (relative to the current
directory, mirroring ``--outdir``), ``kind`` (``sdist`` or ``wheel``), ``size`` in bytes, and ``hashes`` keyed by
algorithm. ``--report`` cannot be combined with ``--metadata``.

To inspect a wheel listed in the report, pass its path straight to ``--metadata``: when the source argument is a
``.whl`` file, build reads ``METADATA`` from the archive and prints it as JSON instead of building anything.

.. code-block:: console

    $ python -m build --report dist/report.json
    $ python -m build --metadata "$(jq -r '.artifacts[] | select(.kind=="wheel") | .path' dist/report.json)"

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
