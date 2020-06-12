************
python-build
************

A simple, correct :pep:`517` package builder
********************************************

python-build will invoke the :pep:`517` hooks to build a distribution package.
It is a simple build tool, it does no dependency management.


The recommended way to invoke is by calling the module:

.. autoprogram:: build.__main__:main_parser()
   :prog: python -m build


But the ``python-build`` script is also available, so that tools such as pipx_
can use it:

.. code-block:: sh

   usage: python-build [-h] ...


By default python-build will build the package in a isolated environment, but
this behavior can be disabled with ``--no-isolation``.


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


Releases
========

You can download a tarball_ from Github, checkout the latest `git tag`_ or fetch
the artifacts from `project page`_ on PyPI.

The recommended way is to checkout the git tags, as they are PGP signed with one
of the following keys:

- |3DCE51D60930EBA47858BA4146F633CBB0EB4BF2|_ *(Filipe Laíns)*


Difference from other tools
===========================


``setup.py sdist bdist_wheel``
------------------------------

``python-build`` is roughly the equivalent of ``setup.py sdist bdist_wheel`` but
with :pep:`517` support.


``python -m pep517.build``
--------------------------

``python-build`` implements a CLI tailored to end users. ``python -m
pep517.build`` *"implements essentially the simplest possible frontend tool,
to exercise and illustrate how the core functionality can be used"*.


Custom Behaviors
================

Fallback Backend
----------------

As recommended in :pep:`517`, if no backend is specified, ``python-build`` will
fallback to ``setuptools.build_meta:__legacy__``.


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

.. _tarball: https://github.com/FFY00/python-build/releases
.. _git tag: https://github.com/FFY00/python-build/tags
.. _project page: https://pypi.org/project/build/


.. |3DCE51D60930EBA47858BA4146F633CBB0EB4BF2| replace:: ``3DCE51D60930EBA47858BA4146F633CBB0EB4BF2``
.. _3DCE51D60930EBA47858BA4146F633CBB0EB4BF2: https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3dce51d60930eba47858ba4146f633cbb0eb4bf2
