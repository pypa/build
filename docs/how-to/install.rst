##############
 Installation
##############

******************
 Installing build
******************

The recommended way to install build is using `uv <https://docs.astral.sh/uv/>`_, but you can also install it via `pip
<https://pip.pypa.io/>`_ or `pipx <https://pipx.pypa.io/>`_:

.. tab:: uv

    .. code-block:: console

        $ uv tool install build

.. tab:: pipx

    .. code-block:: console

        $ pipx install build

.. tab:: pip

    .. code-block:: console

        $ pip install build

Optional Dependencies
=====================

build supports optional extras for different use cases:

- ``build[virtualenv]`` - Use `virtualenv <https://virtualenv.pypa.io/>`_ for isolation instead of `venv
  <https://docs.python.org/3/library/venv.html>`_. This can be useful when using automation tools that rely on
  virtualenv (such as `tox <https://tox.wiki/>`_), or when your operating system's Python package does not include venv
  in the standard installation.

  .. code-block:: console

      $ pip install 'build[virtualenv]'

- ``build[uv]`` - Bundle `uv <https://docs.astral.sh/uv/>`_ for use with ``--installer=uv`` if you don't have another
  install of uv available.

  .. code-block:: console

      $ pip install 'build[uv]'

************************
 Verifying Attestations
************************

`Attestations <https://github.com/pypa/build/attestations>`_ are available after 1.2.1 and can be verified with the
``gh`` CLI tool:

.. code-block:: sh

    $ python -m pip --no-cache-dir download --no-deps build
    $ gh attestation verify build*.whl --repo pypa/build

`PEP 740 <https://peps.python.org/pep-0740/>`_ has been accepted. Support for PEP 740 attestations in build is being
tracked in :issue:`987`.

**********************
 Installing via conda
**********************

On conda-forge, this package is called python-build_, therefore it can be installed via conda_ or an equivalent:

.. code-block:: sh

    $ conda install conda-forge::python-build

***************
 Bootstrapping
***************

This package can build itself only with the `tomli <https://github.com/hukkin/tomli>`_ (can be omitted in Python 3.11+)
and `pyproject-hooks <https://github.com/pypa/pyproject-hooks>`_ dependencies. The ``--skip-dependency-check`` flag
should be used in this case.

***************
 Compatibility
***************

``build`` is verified to be compatible with the following Python versions:

- 3.10
- 3.11
- 3.12
- 3.13
- 3.14
- PyPy 3.10
- PyPy 3.11

.. _conda: https://github.com/conda/conda

.. _python-build: https://github.com/conda-forge/python-build-feedstock

.. |3DCE51D60930EBA47858BA4146F633CBB0EB4BF2| replace:: ``3DCE51D60930EBA47858BA4146F633CBB0EB4BF2``

.. _3dce51d60930eba47858ba4146f633cbb0eb4bf2: https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3dce51d60930eba47858ba4146f633cbb0eb4bf2
