:hide-toc:

*****
build
*****

A simple, correct :pep:`517` package builder.

build will invoke the :pep:`517` hooks to build a distribution package.
It is a simple build tool and does not perform any dependency management.

.. code-block::

   python -m build . --sdist --wheel

This will build the package in an isolated environment, generating a
source-distribution and wheel in the directory ``dist/``.

.. toctree::
   :hidden:

   mission
   differences

.. toctree::
   :caption: Usage
   :hidden:

   installation
   cli
   api

   Source Code <https://github.com/pypa/build/>
   Issue Tracker <https://github.com/pypa/build/issues>
