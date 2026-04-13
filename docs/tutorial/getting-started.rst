#################
 Getting Started
#################

This tutorial will guide you through installing build and creating your first Python package ready for distribution.

.. note::

    New to Python packaging? Start with the `Python Packaging User Guide tutorial
    <https://packaging.python.org/en/latest/tutorials/packaging-projects/>`_ to learn how to structure a Python project.
    This tutorial assumes you already have a project with a ``pyproject.toml`` file.

***************
 Prerequisites
***************

You need Python 3.10 or later installed on your system. Check your Python version:

.. code-block:: console

    $ python --version
    Python 3.11.0

**************
 Installation
**************

The recommended way to install build is using pip:

.. code-block:: console

    $ pip install build

Or, if you prefer to install it in an isolated environment using pipx:

.. code-block:: console

    $ pipx install build

For corporate environments or systems with restricted internet access, see :doc:`../how-to/corporate-environments`.

***************************
 Creating a simple package
***************************

Let's create a minimal Python package to demonstrate how build works.

1. Create a project directory:

.. code-block:: console

    $ mkdir mypackage
    $ cd mypackage

2. Create a ``pyproject.toml`` file:

.. code-block:: toml

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [project]
    name = "mypackage"
    version = "0.1.0"
    description = "A simple example package"
    readme = "README.md"
    requires-python = ">=3.8"

3. Create a ``README.md`` file:

.. code-block:: markdown

    # My Package

    This is a simple example package.

4. Create your Python package:

.. code-block:: console

    $ mkdir src/mypackage
    $ touch src/mypackage/__init__.py

5. Add some code to ``src/mypackage/__init__.py``:

.. code-block:: python

    def hello():
        return "Hello from mypackage!"

***********************
 Building your package
***********************

Now you're ready to build your package:

.. code-block:: console

    $ python -m build

You should see output like:

.. code-block:: console

    * Creating isolated environment: venv+pip...
    * Installing packages in isolated environment:
      - hatchling
    * Getting build dependencies for sdist...
    * Building sdist...
    * Building wheel from sdist
    * Creating isolated environment: venv+pip...
    * Installing packages in isolated environment:
      - hatchling
    * Getting build dependencies for wheel...
    * Building wheel...
    Successfully built mypackage-0.1.0.tar.gz and mypackage-0.1.0-py3-none-any.whl

The built packages are now in the ``dist/`` directory:

.. code-block:: console

    $ ls dist/
    mypackage-0.1.0-py3-none-any.whl
    mypackage-0.1.0.tar.gz

*****************************
 Understanding what happened
*****************************

Build created two `distribution files <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_
(packages ready for distribution):

1. **Source distribution**: ``mypackage-0.1.0.tar.gz``

   This `tarball <https://en.wikipedia.org/wiki/Tar_(computing)>`_ (compressed archive) contains your source code.
   Anyone can download it and build your package on their system. Learn more in the `source distribution specification
   <https://packaging.python.org/en/latest/specifications/source-distribution-format/>`_.

2. **Wheel**: ``mypackage-0.1.0-py3-none-any.whl``

   This `wheel <https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_ is a pre-built
   package that `pip <https://pip.pypa.io/>`_ can install directly without needing to build anything. This makes
   installation much faster.

Build used an **isolated environment** to ensure your package builds consistently regardless of what you have installed
on your computer. It:

1. Created a temporary `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_
2. Installed only your build dependencies (`hatchling <https://hatch.pypa.io/latest/>`_)
3. Invoked the **build backend** to create the distribution files
4. Cleaned up the temporary environment when done

************
 Next steps
************

- Learn about :doc:`../how-to/basic-usage` for common build workflows
- Understand :doc:`../explanation/how-it-works` for details on the build process
- See :doc:`../how-to/config-settings` to customize your build
