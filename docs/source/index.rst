:hide-toc:

*****
build
*****

A simple, correct :pep:`517` package builder.

build will invoke the :pep:`517` hooks to build a distribution package.
It is a simple build tool and does not perform any dependency management.

.. autoprogram:: build.__main__:main_parser()
   :prog: python -m build

.. note::

   A ``pyproject-build`` CLI script is also available, so that tools such as pipx_
   can use it.

By default build will build the package in a isolated
environment, but this behavior can be disabled with `--no-isolation`.

.. toctree::
   :hidden:

   mission
   differences

.. toctree::
   :caption: Usage
   :hidden:

   installation
   api

   Source Code <https://github.com/pypa/build/>
   Issue Tracker <https://github.com/pypa/build/issues>

.. _pipx: https://github.com/pipxproject/pipx
