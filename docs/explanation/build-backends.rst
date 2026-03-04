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

Your ``pyproject.toml`` specifies which backend to use in the ``[build-system]`` section. For example, using hatchling
as the backend looks like this:

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

Several build backends are available, each with different features and philosophies.

setuptools
==========

setuptools is the traditional and most widely used build backend. It has extensive features and backwards compatibility
with older packaging standards, making it suitable for complex projects and projects that need to maintain compatibility
with older tooling.

To use setuptools, configure your ``pyproject.toml`` like this:

.. code-block:: toml

    [build-system]
    requires = ["setuptools>=61.0", "wheel"]
    build-backend = "setuptools.build_meta"

setuptools excels at handling complex build requirements including C extensions, namespace packages, and entry points.
However, it can be complex to configure correctly and has many legacy features that may be confusing.

See the `setuptools documentation <https://setuptools.pypa.io/>`_ for details.

hatchling
=========

hatchling is the build backend from the Hatch project. It provides a modern, user-friendly interface with sensible
defaults and good performance.

To use hatchling:

.. code-block:: toml

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

hatchling works well for pure Python packages and has excellent plugin support for extending functionality. It
emphasizes convention over configuration and includes built-in support for common patterns like src-layout and editable
installs. The main limitation is that it's newer and may have less community documentation than setuptools.

See the `hatchling documentation <https://hatch.pypa.io/latest/config/build/>`_ for details.

flit-core
=========

flit-core is a minimalist build backend that focuses on simplicity for pure Python packages.

To use flit-core:

.. code-block:: toml

    [build-system]
    requires = ["flit-core>=3.2"]
    build-backend = "flit_core.buildapi"

flit-core works best for simple, pure Python packages without complex build requirements. It has minimal configuration
and fast build times. By default, it includes all files tracked by git in the source distribution. The trade-off is
limited support for complex scenarios like C extensions or non-standard package layouts.

See the `flit documentation <https://flit.pypa.io/>`_ for details.

pdm-backend
===========

pdm-backend is the build backend from the PDM project, offering modern features and good integration with PEP 621
metadata.

To use pdm-backend:

.. code-block:: toml

    [build-system]
    requires = ["pdm-backend"]
    build-backend = "pdm.backend"

pdm-backend provides strong PEP 621 support, good handling of dynamic metadata, and support for both pure Python and
extension modules. It's actively developed and includes features like SCM versioning and custom build hooks.

See the `pdm-backend documentation <https://pdm-backend.fming.dev/>`_ for details.

poetry-core
===========

poetry-core is the build backend extracted from Poetry. It's designed primarily for use with the Poetry tool but can be
used standalone.

To use poetry-core:

.. code-block:: toml

    [build-system]
    requires = ["poetry-core"]
    build-backend = "poetry.core.masonry.api"

poetry-core handles pure Python packages well and integrates tightly with Poetry's ecosystem. However, configuration is
done through Poetry's custom ``[tool.poetry]`` section rather than standard ``[project]`` metadata, which can reduce
interoperability with other tools.

See the `poetry documentation <https://python-poetry.org/>`_ for details.

scikit-build-core
=================

scikit-build-core is a build backend specifically designed for projects with CMake-based C/C++ extensions.

To use scikit-build-core:

.. code-block:: toml

    [build-system]
    requires = ["scikit-build-core"]
    build-backend = "scikit_build_core.build"

scikit-build-core provides excellent CMake integration, cross-platform compilation support, and modern PEP 621 metadata
support. It's the recommended backend for projects using CMake for extension modules, replacing the older scikit-build.

See the `scikit-build-core documentation <https://scikit-build-core.readthedocs.io/>`_ for details.

meson-python
============

meson-python is a build backend for projects using the Meson build system, particularly useful for compiled extensions.

To use meson-python:

.. code-block:: toml

    [build-system]
    requires = ["meson-python"]
    build-backend = "mesonpy"

meson-python offers fast builds, excellent cross-platform support, and good integration with Meson's dependency
management. It's especially strong for projects with complex compiled components and is increasingly popular in the
scientific Python ecosystem.

See the `meson-python documentation <https://meson-python.readthedocs.io/>`_ for details.

********************
 Choosing a Backend
********************

The right backend depends on your project's needs. For simple pure Python packages, flit-core or hatchling provide
straightforward configuration and fast builds. Projects that need extensive customization or have complex requirements
often benefit from setuptools' mature feature set and extensive documentation.

If your project includes C or C++ extensions built with CMake, scikit-build-core is the natural choice. For projects
using Meson for compilation, meson-python provides the best integration. Projects already using Poetry might prefer
poetry-core for consistency, though this limits interoperability with other tools.

New projects without special requirements should consider hatchling or flit-core for their modern approach and
simplicity. Existing projects using setuptools can continue doing so, as it remains well-maintained and
feature-complete.

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

build allows passing configuration settings to backends via the ``--config-setting`` or ``-C`` flag. The syntax and
available options depend entirely on the backend.

For example, with setuptools you might pass build options:

.. code-block:: console

    $ python -m build -C--build-option=--build-number=123

With scikit-build-core, you can configure CMake:

.. code-block:: console

    $ python -m build -Ccmake.define.BUILD_TESTING=OFF

Each backend interprets these settings differently. See :doc:`../how-to/config-settings` for backend-specific examples.

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

**These commands do not work with build**: build uses the PEP 517 interface, which only defines hooks for building
distributions (``build_wheel`` and ``build_sdist``). It does not support arbitrary setuptools commands.

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
