################
 Build Backends
################

This document explains what build backends are, how they work with build, and how to choose the right one for your
project.

**************************
 What is a Build Backend?
**************************

A **build backend** is a Python package that knows how to build your project into `distributable formats
<https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_ (`source distributions
<https://packaging.python.org/en/latest/specifications/source-distribution-format/>`_ and `wheels
<https://packaging.python.org/en/latest/specifications/binary-distribution-format/>`_). The backend implements a
standardized interface defined in :PEP:`517`, which build (the **frontend**) uses to create your package distributions.

When you run ``python -m build``, the frontend (build) reads your `pyproject.toml
<https://packaging.python.org/en/latest/specifications/pyproject-toml/>`_ to determine which backend to use, then
invokes that backend to perform the actual building. The separation between frontend and backend allows different
projects to use different build systems (like `setuptools <https://setuptools.pypa.io/>`_, `hatchling
<https://hatch.pypa.io/latest/>`_, or `flit <https://flit.pypa.io/>`_) while all working with the same frontend tool.

******************************
 How Backends Work with build
******************************

The relationship between build and backends follows a clear contract:

.. mermaid::

    %%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#4051b5','primaryTextColor':'#fff','primaryBorderColor':'#2c3e8f','lineColor':'#5468c4','secondaryColor':'#7c8fd6','tertiaryColor':'#e8eaf6'}}}%%
    flowchart TD
        subgraph Frontend["Build Frontend (build)"]
            A[CLI Interface]
            B[Read pyproject.toml]
            C[Create Isolation]
            D[Invoke Hooks]
        end

        subgraph Backend["Build Backend (setuptools/hatchling/flit/...)"]
            E[Package Discovery]
            F[File Inclusion]
            G[Metadata Generation]
            H[Create Distributions]
        end

        A --> B
        B --> C
        C --> D
        D -->|PEP 517 Hooks| E
        E --> F
        F --> G
        G --> H
        H -->|sdist & wheel| I[dist/]

        style Frontend fill:#e8eaf6,stroke:#4051b5,color:#000
        style Backend fill:#fff3e0,stroke:#f57c00,color:#000
        style I fill:#2e7d32,stroke:#1b5e20,color:#fff

Your ``pyproject.toml`` specifies which backend to use in the `build-system declaration
<https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#declaring-the-build-backend>`_. For example,
using hatchling as the backend looks like this:

.. code-block:: toml

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

The ``requires`` field lists the packages needed to perform a build, which build installs in an isolated environment.
The ``build-backend`` field specifies the Python import path to the backend object that implements the PEP 517
interface.

When building, build creates an isolated environment, installs the required packages, imports the backend module, and
calls standardized hook functions like ``build_wheel()`` or ``build_sdist()``. The backend then creates the distribution
files and returns their filenames.

**************************
 Available Build Backends
**************************

See :ref:`backend-documentation` for links to backend guides and configuration references.

.. raw:: html

    <span id="id1"></span>
    <span id="id2"></span>
    <span id="flit-core"></span>
    <span id="meson-python"></span>
    <span id="pdm-backend"></span>
    <span id="poetry-core"></span>
    <span id="scikit-build-core"></span>

********************
 Choosing a Backend
********************

Follow `Choosing a build backend
<https://packaging.python.org/en/latest/tutorials/packaging-projects/#choosing-a-build-backend>`_ in the Python
Packaging User Guide. Backend capabilities and configuration belong to the backend's own documentation.

**********************
 Configuring Backends
**********************

Each backend has its own configuration approach. Modern backends use the ``[project]`` section of ``pyproject.toml`` for
metadata following PEP 621. Backend-specific settings go in a ``[tool.backend-name]`` section.

For example, with hatchling you might have:

.. code-block:: toml

    [project]
    name = "mypackage"
    version = "1.0.0"

    [tool.hatch.build]
    include = ["src/**/*.py"]

With setuptools:

.. code-block:: toml

    [project]
    name = "mypackage"
    version = "1.0.0"

    [tool.setuptools.packages.find]
    where = ["src"]

Always consult your backend's documentation for configuration options. Common configuration needs include specifying
which files to include, where to find packages, how to handle version numbers, and how to process extension modules.

*****************************
 Passing Options to Backends
*****************************

See :doc:`../how-to/config-settings` for the ``-C`` syntax, empty values, and backend-specific examples.

******************
 Dynamic Metadata
******************

Some backends support generating metadata dynamically at build time. Common use cases include reading version numbers
from git tags, generating file lists from directory contents, or computing dependencies based on environment.

Most backends support version from SCM (source control management). For example, with hatchling using hatch-vcs:

.. code-block:: toml

    [build-system]
    requires = ["hatchling", "hatch-vcs"]
    build-backend = "hatchling.build"

    [tool.hatch.version]
    source = "vcs"

The backend reads version information from git tags during the build. This keeps version numbers in sync between git and
your package without manual updates.

Dynamic metadata is powerful but has trade-offs. It can make builds less reproducible if not carefully managed, and it
may prevent installation from sdists if the dynamic information source (like git) isn't available.

********************************
 Backend Extensions and Plugins
********************************

Many backends support plugins to extend functionality. setuptools has an extensive plugin ecosystem including plugins
for namespace packages, entry points, and custom build steps. hatchling has a plugin system for custom build hooks,
version sources, and metadata providers.

When choosing a backend, consider whether you need extensibility through plugins. If your project has unique build
requirements, a backend with a strong plugin system may be beneficial even if it's more complex to configure initially.

********************
 Switching Backends
********************

Switching from one backend to another is possible but requires care. The main steps involve updating your
``[build-system]`` section in ``pyproject.toml``, migrating configuration from the old backend's format to the new one,
and testing that the built distributions are equivalent.

When migrating, always build and inspect both sdist and wheel to verify all files are included correctly. Test
installation from both distribution types. Check that metadata (version, dependencies, entry points) is correctly
preserved.

Most migrations involve moving from setuptools to a modern backend. The new backend's documentation typically includes
migration guides. Common challenges include differences in how package discovery works, how data files are included, and
how version numbers are specified.

*********************
 Backend Development
*********************

For most users, using an existing backend is the right choice. However, if you have unique requirements not met by any
existing backend, you can implement your own PEP 517 backend.

A minimal backend must implement these functions in a Python module:

.. code-block:: python

    def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
        # Build wheel, return filename
        pass


    def build_sdist(sdist_directory, config_settings=None):
        # Build sdist, return filename
        pass

Implementing a full-featured backend requires handling metadata extraction, dependency specification, editable installs,
and error handling. Unless you have very specialized needs, contributing to an existing backend or using its plugin
system is usually more practical than creating a new one.

***********************************************
 Why setuptools commands don't work with build
***********************************************

If you're migrating from ``setup.py``, you may be used to running commands like:

.. code-block:: console

    $ python setup.py clean
    $ python setup.py test
    $ python setup.py develop

**These commands do not work with build**: build invokes standardized backend hooks and does not accept arbitrary
setuptools commands.

**Modern alternatives**:

- **clean**: Remove the ``dist/`` directory manually or let your CI do it
- **test**: Use ``pytest`` directly or via ``tox``
- **develop**: Use ``pip install --editable .`` for editable installs
- **sdist/bdist_wheel**: Use ``python -m build``

If you need custom build steps, implement them in your build backend's hooks or use a plugin system. For example,
setuptools supports ``setup.py`` with custom build steps that run during the PEP 517 build process.

**********
 See also
**********

- :doc:`how-it-works` for how build invokes backends
- :doc:`../how-to/config-settings` for backend-specific configuration examples
- `PEP 517 <https://peps.python.org/pep-0517/>`_ for the backend interface specification
- `PEP 621 <https://peps.python.org/pep-0621/>`_ for standard project metadata
