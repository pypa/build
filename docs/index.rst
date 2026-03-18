*****
build
*****

A simple, correct `Python packaging <https://packaging.python.org/>`_ **build frontend**.

build reads your project's `pyproject.toml configuration file <https://packaging.python.org/en/latest/specifications/pyproject-toml/>`_ and invokes **build backends** to create `distribution packages <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_—the files you upload to `PyPI <https://pypi.org/>`_ or install with pip. It focuses solely on building packages and does not manage dependencies or virtual environments.

Mission Statement
=================

Many Python tools combine multiple capabilities into one project. For example, pip_ both installs packages and can build them. While convenient, this tight coupling isn't always desirable. Some users need standalone build tools for custom environments (outside PyPI_), or they manage packages themselves (like Linux distributions do).

This project fills that gap by providing a standalone build tool following modern Python packaging standards for how build tools communicate with backends and how ``pyproject.toml`` defines build requirements.

We keep dependencies minimal to make build easy to install and use in restricted environments.

Differences from other tools
=============================

Thanks to standardization, all compliant build frontends produce the same outputs (`source distributions <https://packaging.python.org/en/latest/specifications/source-distribution-format/>`_ and `wheels <https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_) from the same project. The differences are mainly in scope, dependencies, and extra features.

``uv build``
------------

`uv build <https://docs.astral.sh/uv/>`_ is essentially equivalent to ``python -m build --installer=uv``. Both follow packaging standards. build offers features like ``--config-json`` for passing complex nested configuration to backends, and the pip installer works on systems that don't have pre-compiled uv wheels.

``setup.py sdist bdist_wheel``
-------------------------------

build is the modern equivalent of ``setup.py sdist bdist_wheel``, supporting any backend — not just `setuptools <https://setuptools.pypa.io/>`_.

``hatch build``
---------------

`hatch build <https://hatch.pypa.io/>`_ is the build command from the Hatch project management tool. It provides a convenient wrapper around the build process as part of the larger Hatch ecosystem for managing Python projects, while build is a standalone tool focused solely on building.

``flit build``
--------------

`flit build <https://flit.pypa.io/>`_ is the build command from the Flit project. One important difference: flit-core produces slightly different source distributions when built by flit itself compared to other frontends. Using build (or any standards-compliant frontend) ensures consistent outputs regardless of the backend.

``cibuildwheel``
----------------

`cibuildwheel <https://cibuildwheel.pypa.io/>`_ is a different kind of tool. While build creates a single wheel for the current platform, cibuildwheel orchestrates building wheels across many platforms and Python versions in CI. It actually calls a build frontend (like build or pip) internally for each platform. Use build to create a pure-Python wheel or a single native wheel; use cibuildwheel when you need to produce native wheels for many platforms.

Where to start
==============

**First time using build?** Start with the :doc:`tutorial/getting-started` to create your first package.

**Need to solve a specific problem?** Check the :doc:`how-to/basic-usage` for common workflows, or browse the how-to guides below for your specific scenario.

**Looking for technical details?** The :doc:`reference/cli` documents all command-line options, and the :doc:`reference/api` covers the Python API.

**Want to understand how it works?** Read :doc:`explanation/how-it-works` to learn about the build process and isolation.

.. toctree::
   :caption: Tutorial
   :hidden:

   tutorial/getting-started

.. toctree::
   :caption: How-to Guides
   :hidden:

   how-to/install
   how-to/basic-usage
   how-to/choosing-tools
   how-to/ci-cd
   how-to/corporate-environments
   how-to/config-settings
   how-to/troubleshooting

.. toctree::
   :caption: Reference
   :hidden:

   reference/cli
   reference/api
   reference/environment-variables

.. toctree::
   :caption: Explanation
   :hidden:

   explanation/how-it-works
   explanation/build-backends

.. toctree::
   :caption: Development
   :hidden:

   development/contributing
   development/release

.. toctree::
   :caption: Project
   :hidden:

   changelog
   Source Code <https://github.com/pypa/build/>
   Issue Tracker <https://github.com/pypa/build/issues>

.. _pip: https://github.com/pypa/pip
.. _PyPI: https://pypi.org/
.. _pipx: https://github.com/pipxproject/pipx
