###################
 API Documentation
###################

build provides a Python API for programmatic use in build tools, CI systems, and automation scripts.

*************
 Basic Usage
*************

Building a package programmatically:

.. code-block:: python

    from build import ProjectBuilder

    builder = ProjectBuilder("path/to/project")
    builder.build("wheel", "dist/")

Building both sdist and wheel:

.. code-block:: python

    from build import ProjectBuilder

    builder = ProjectBuilder(".")
    builder.build("sdist", "dist/")
    builder.build("wheel", "dist/")

Using isolated environments (default):

.. code-block:: python

    from build import ProjectBuilder
    from build.env import IsolatedEnvBuilder

    with IsolatedEnvBuilder() as env:
        builder = ProjectBuilder(".", runner=env.runner)
        builder.build("wheel", "dist/")

Disabling isolation:

.. code-block:: python

    from build import ProjectBuilder

    builder = ProjectBuilder(".", runner=lambda cmd, **kwargs: None)
    builder.build("wheel", "dist/")

Getting package metadata without building:

.. code-block:: python

    from build import ProjectBuilder

    builder = ProjectBuilder(".")
    metadata = builder.metadata
    print(f"Package: {metadata.name} {metadata.version}")

Accessing build dependencies:

.. code-block:: python

    from build import ProjectBuilder

    builder = ProjectBuilder(".")
    requires = builder.build_system_requires
    print(f"Build requires: {requires}")

    # Get additional dependencies for building a wheel
    wheel_requires = builder.get_requires_for_build("wheel")
    print(f"Wheel build requires: {wheel_requires}")

Handling errors:

.. code-block:: python

    from build import ProjectBuilder
    from build import BuildException

    try:
        builder = ProjectBuilder(".")
        builder.build("wheel", "dist/")
    except BuildException as e:
        print(f"Build failed: {e}")

***********
 Reference
***********

******************
 ``build`` module
******************

.. automodule:: build
    :members:
    :undoc-members:
    :show-inheritance:

**********************
 ``build.env`` module
**********************

.. automodule:: build.env
    :members:
    :undoc-members:
    :show-inheritance:

***********************
 ``build.util`` module
***********************

.. automodule:: build.util
    :members:
    :undoc-members:
    :show-inheritance:
