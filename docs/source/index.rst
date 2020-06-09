************
python-build
************

A simple, correct :pep:`517` package builder
********************************************

python-build will invoke the :pep:`517` hooks to build a distribution package.
It is a simple build tool, it does no dependency management.


The recommended way to invoke is by calling the module:

.. code-block:: sh

   $ python -m build
   usage: python -m build [-h] [--sdist] [--wheel] [--outdir ./dist] [--skip-dependencies] [.]

   positional arguments:
   .                     source directory (defaults to current directory)

   optional arguments:
   -h, --help            show this help message and exit
   --sdist, -s           build a source package
   --wheel, -w           build a wheel
   --outdir ./dist, -o ./dist
                           output directory
   --skip-dependencies, -x
                           does not check for the dependencies


But the ``python-build`` script is also available, so that tools such as pipx_
can use it:

.. code-block:: sh

   $ python-build
   usage: python-build [-h] ...


Mission Statement
=================

The in the Python ecosystem, the build system tools and the package management
are very intertwined. While it might be useful for user to be able to access
all this capabilities in a single project (such as pip_), there are several use-
cases where this is not desirable. The main being custom environments (outside
PyPI_) or situations where the user does its own package management, such as
Linux distributions.

This project aims to fit the "building packages hole" for such use-cases in
:pep:`517`/:pep:`518` workflows.

As it is intended to be used by users that do their own package management,
we will try to keep dependencies to a minimum, in order to try make
bootstrapping easier.


Bootstrapping
=============

This package can build itself with only the ``toml`` and ``pep517``
dependencies. The ``--skip-dependencies`` flag should be used in this case.


Compability
===========

``python-build`` is verified to be compatible with the following Python
versions:
  - 2.7
  - 3.5
  - 3.6
  - 3.7
  - 3.8


``build`` module
================

.. toctree::
   :maxdepth: 2

   API Documentation <modules>


.. _pipx: https://github.com/pipxproject/pipx
.. _pip: https://github.com/pypa/pip
.. _PyPI: https://pypi.org/
