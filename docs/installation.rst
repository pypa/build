============
Installation
============

You can download a tarball_ from Github, checkout the latest `git tag`_ or fetch
the artifacts from `project page`_ on PyPI.

``build`` may also be installed via `pip`_ or an equivalent:

.. code-block:: sh

   $ pip install build

The recommended way is to checkout the git tags, as they are PGP signed with one
of the following keys:

- |3DCE51D60930EBA47858BA4146F633CBB0EB4BF2|_ *(Filipe Laíns)*

Bootstrapping
=============

This package can build itself with only the ``toml`` and ``pep517``
dependencies. The ``--skip-dependencies`` flag should be used in this
case.


Compatibility
=============

``build`` is verified to be compatible with the following Python
versions:

- 2.7
- 3.5
- 3.6
- 3.7
- 3.8
- PyPy(2)
- PyPy3


.. _pipx: https://github.com/pipxproject/pipx
.. _pip: https://github.com/pypa/pip
.. _PyPI: https://pypi.org/

.. _tarball: https://github.com/pypa/build/releases
.. _git tag: https://github.com/pypa/build/tags
.. _project page: https://pypi.org/project/build/


.. |3DCE51D60930EBA47858BA4146F633CBB0EB4BF2| replace:: ``3DCE51D60930EBA47858BA4146F633CBB0EB4BF2``
.. _3DCE51D60930EBA47858BA4146F633CBB0EB4BF2: https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3dce51d60930eba47858ba4146f633cbb0eb4bf2
