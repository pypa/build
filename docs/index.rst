:hide-toc:

*****
build
*****

A simple, correct Python packaging :std:term:`build frontend <Build Frontend>`.

build manages ``pyproject.toml``-based builds, invoking
:std:term:`build-backend <Build Backend>` hooks as appropriate to build a
:std:term:`distribution package <Distribution Package>`.
It is a simple build tool and does not perform any dependency management.

.. sphinx_argparse_cli::
  :module: build.__main__
  :func: main_parser
  :prog: python -m build
  :title: python -m build
  :usage_width: 97

.. note::

   A ``pyproject-build`` CLI script is also available, so that tools such as pipx_
   can use it.

By default build will build the package in an isolated
environment, but this behavior can be disabled with ``--no-isolation``.

.. toctree::
   :hidden:

   mission
   differences

.. toctree::
   :caption: Usage
   :hidden:

   installation
   changelog
   api

.. toctree::
   :caption: Contributing
   :hidden:

   test_suite
   release

.. toctree::
   :caption: Project Links
   :hidden:

   Source Code <https://github.com/pypa/build/>
   Issue Tracker <https://github.com/pypa/build/issues>

.. _pipx: https://github.com/pipxproject/pipx
