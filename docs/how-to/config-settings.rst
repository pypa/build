#######################
 Backend Configuration
#######################

The ``--config-setting`` (or ``-C``) flag allows you to pass options to your **build backend**. The syntax and available
options depend entirely on which backend you're using (e.g., `setuptools <https://setuptools.pypa.io/>`_, hatchling,
`flit <https://flit.pypa.io/>`_).

.. important::

    The ``--config-setting`` flag passes options to the **build backend** that actually builds your package, not to
    build itself. Different backends accept different options. Check your backend's documentation for available
    settings.

**************
 Basic syntax
**************

The basic syntax is:

.. code-block:: console

    $ python -m build -C KEY=VALUE

Or for options without values (equivalent to ``-C KEY=""``):

.. code-block:: console

    $ python -m build -C KEY

.. note::

    The ``-C KEY`` syntax (without ``=``) is supported by build but not by pip. For maximum compatibility, use ``-C
    KEY=""`` explicitly when you need an empty value.

Multiple settings can be provided:

.. code-block:: console

    $ python -m build -C KEY1=VALUE1 -C KEY2=VALUE2

************
 Setuptools
************

Setuptools requires a special ``--build-option`` wrapper for most settings.

Build numbers
=============

To add a build number to your wheel:

.. code-block:: console

    $ python -m build --wheel \
        -C--build-option=bdist_wheel \
        -C--build-option=--build-number \
        -C--build-option=123

This creates a wheel named ``package-1.0.0-123-py3-none-any.whl``.

Compiler selection
==================

To specify a compiler on Windows:

.. code-block:: console

    $ python -m build \
        -C--build-option=build_ext \
        -C--build-option=--compiler \
        -C--build-option=mingw32

.. note::

    Each argument must be a separate ``-C`` flag. Setuptools processes these as separate command-line arguments.

Getting help
============

To see available setuptools build options:

.. code-block:: console

    $ python -m build -C--build-option=--help

*******************
 scikit-build-core
*******************

scikit-build-core uses a more intuitive dotted syntax.

CMake options
=============

.. code-block:: console

    $ python -m build \
        -Ccmake.define.BUILD_TESTING=OFF \
        -Ccmake.define.CMAKE_BUILD_TYPE=Release

Logging
=======

.. code-block:: console

    $ python -m build -Clogging.level=INFO

Install target
==============

.. code-block:: console

    $ python -m build -Cinstall.strip=false

Multiple options:

.. code-block:: console

    $ python -m build \
        -Clogging.level=DEBUG \
        -Ccmake.define.USE_CUDA=ON \
        -Cinstall.components=runtime

**************
 meson-python
**************

Meson-python passes options directly to meson.

Setup options
=============

.. code-block:: console

    $ python -m build -Csetup-args=-Doption=value

Compile options
===============

.. code-block:: console

    $ python -m build \
        -Csetup-args=-Dbuildtype=release \
        -Csetup-args=-Db_ndebug=true

***********
 hatchling
***********

Hatchling supports various build options.

Reproducible builds
===================

.. code-block:: console

    $ python -m build -Creproducible=true

Shared data
===========

.. code-block:: console

    $ python -m build -Cshared-data=/custom/path

***********
 flit-core
***********

Flit-core has minimal configuration options as it focuses on simplicity.

*************
 poetry-core
*************

Poetry-core currently does not support configuration settings via the command line.

*************************
 Using ``--config-json``
*************************

For complex nested configuration, use ``--config-json`` instead:

.. code-block:: console

    $ python -m build --config-json='{"cmake": {"define": {"VAR1": "value1", "VAR2": "value2"}}}'

This is particularly useful in CI/CD scripts where configuration can be generated programmatically.

.. note::

    ``--config-setting`` and ``--config-json`` cannot be used together.

***************
 Common Issues
***************

Options starting with hyphens
=============================

If your option starts with a hyphen, you must use the ``=`` syntax to prevent build from interpreting it as its own
flag:

.. code-block:: console

    $ python -m build -C=--my-setting

Not ``-C --my-setting`` which would fail.

Backend not recognizing options
===============================

If your backend doesn't recognize an option:

1. Check your backend's documentation for the correct syntax
2. Verify you're using the latest version of the backend
3. Some backends only support certain options in newer versions

*******************************
 Finding backend documentation
*******************************

- `Setuptools <https://setuptools.pypa.io/>`_
- `scikit-build-core <https://scikit-build-core.readthedocs.io/>`_
- `meson-python <https://meson-python.readthedocs.io/>`_
- `hatchling <https://hatch.pypa.io/latest/config/build/>`_
- `flit-core <https://flit.pypa.io/>`_
- `poetry-core <https://python-poetry.org/docs/>`_
- `pdm-backend <https://pdm-backend.fming.dev/>`_

**********
 See also
**********

- :doc:`basic-usage` for general build commands
- :doc:`../reference/cli` for all command-line options
- :doc:`../explanation/build-backends` to understand how backends work
