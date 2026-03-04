*****
build
*****

A simple, correct `Python packaging <https://packaging.python.org/>`_ **build frontend**.

build reads your project's `pyproject.toml configuration file <https://packaging.python.org/en/latest/specifications/pyproject-toml/>`_ and invokes **build backends** to create `distribution packages <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_—the files you upload to `PyPI <https://pypi.org/>`_ or install with pip. It focuses solely on building packages and does not manage dependencies or virtual environments.

Mission Statement
=================

Many Python tools combine multiple capabilities into one project. For example, pip_ both installs packages and can build them. While convenient, this tight coupling isn't always desirable. Some users need standalone build tools for custom environments (outside PyPI_), or they manage packages themselves (like Linux distributions do).

This project fills that gap by providing a standalone build tool following modern Python packaging standards (:pep:`517` defines how build tools communicate with backends, :pep:`518` defines the pyproject.toml configuration format).

We keep dependencies minimal to make build easy to install and use in restricted environments.

Differences from other tools
=============================

``uv build``
------------

`uv build <https://docs.astral.sh/uv/>`_ is essentially equivalent to ``python -m build --installer=uv``. Both create the same outputs (`source distributions <https://packaging.python.org/en/latest/specifications/source-distribution-format/>`_ and `wheels <https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_), but ``uv build`` uses uv's faster dependency installer by default. build provides more flexibility in choosing installers and offers additional options like ``--no-isolation`` for advanced use cases.

``setup.py sdist bdist_wheel``
-------------------------------

build is roughly the equivalent of ``setup.py sdist bdist_wheel`` but with :pep:`517` support, allowing use with projects that don't use `setuptools <https://setuptools.pypa.io/>`_.

``hatch build``
---------------

`hatch build <https://hatch.pypa.io/>`_ is the build command from the Hatch project management tool. Like ``uv build``, it provides a convenient wrapper around the build process. build is a standalone tool focused solely on building, while ``hatch build`` is part of the larger Hatch ecosystem for managing Python projects.

``pep517.build``
----------------

build implements a CLI tailored to end users.

`pep517.build <https://pypi.org/project/pep517/>`_ contained a proof-of-concept of a :pep:`517` frontend. It *"implement[ed] essentially the simplest possible frontend tool, to exercise and illustrate how the core functionality can be used"*. It has since been `deprecated and is scheduled for removal <https://github.com/pypa/pep517/pull/83>`_.

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

.. toctree::
   :caption: Project
   :hidden:

   changelog
   Source Code <https://github.com/pypa/build/>
   Issue Tracker <https://github.com/pypa/build/issues>

.. _pip: https://github.com/pypa/pip
.. _PyPI: https://pypi.org/
.. _pipx: https://github.com/pipxproject/pipx
