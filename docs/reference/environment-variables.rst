#######################
 Environment Variables
#######################

This reference documents environment variables that affect build's behavior. You can use these to configure private
package indexes, proxies, SSL certificates, and other settings.

************************
 Variables Set by build
************************

``PATH`` and ``PYTHONPATH``
===========================

For isolated backend subprocesses, build prepends the environment's scripts directory to ``PATH`` and sets
``PYTHONPATH`` to an empty string so host import paths do not leak into the build.

``VIRTUAL_ENV``
===============

When using the uv installer, build sets ``VIRTUAL_ENV`` for the dependency-installation subprocess to identify the
target environment. It does not set this variable for backend hooks, so backends should not rely on it to identify
build's isolated environment.

*****************************
 Package Index Configuration
*****************************

By default, build uses `pip <https://pip.pypa.io/>`_ to install build dependencies in isolated environments. Configure
pip using these environment variables to work with private package indexes or mirrors. For detailed examples, see
:doc:`../how-to/corporate-environments`.

.. note::

    These ``PIP_*`` variables only apply when using the default pip installer. When using ``--installer=uv``, configure
    uv through its own `environment variables <https://docs.astral.sh/uv/configuration/environment/>`_ instead (e.g.,
    ``UV_INDEX_URL``, ``UV_EXTRA_INDEX_URL``).

``PIP_INDEX_URL``
=================

Sets the primary `package index <https://packaging.python.org/en/latest/glossary/#term-Package-Index>`_ URL where pip
looks for packages. Use this to point to private package repositories or PyPI mirrors. Defaults to
``https://pypi.org/simple``.

See :doc:`../how-to/corporate-environments` for private-index setup.

``PIP_EXTRA_INDEX_URL``
=======================

Adds additional package indexes to search beyond the primary index. This allows using both `PyPI <https://pypi.org/>`_
and a private index simultaneously.

.. warning::

    Combining indexes risks dependency confusion: a package on one index can shadow a package on another. Prefer a
    single trusted index with ``PIP_INDEX_URL``. See :doc:`../how-to/corporate-environments` for private-index setup.

``PIP_CERT``
============

Path to a custom CA certificate bundle for SSL/TLS verification. Use this when your organization uses self-signed
certificates or a custom certificate authority. Defaults to system certificates.

See :ref:`corporate-certificates` for setup instructions.

``PIP_TRUSTED_HOST``
====================

Disables SSL verification for the specified host. Only use this in secure development environments where SSL
certificates aren't available.

Prefer configuring a CA bundle as described in :ref:`corporate-certificates`.

***********************
 Network Configuration
***********************

``PIP_TIMEOUT``
===============

Sets the timeout in seconds for network operations. Increase this on slow or unreliable network connections. Defaults to
15 seconds.

.. code-block:: console

    $ export PIP_TIMEOUT=60
    $ python -m build

``PIP_RETRIES``
===============

Number of times pip retries failed downloads. Increase this on unstable network connections. Defaults to 5 retries.

.. code-block:: console

    $ export PIP_RETRIES=10
    $ python -m build

``PIP_NO_CACHE_DIR``
====================

Disables pip's package cache directory, forcing fresh downloads every time. Useful in CI environments to ensure
completely clean builds, though this makes builds slower.

.. code-block:: console

    $ export PIP_NO_CACHE_DIR=1
    $ python -m build

*********************
 Proxy Configuration
*********************

If you're behind a corporate proxy, configure these variables to route pip's network requests through your proxy server.
Both uppercase and lowercase versions are recognized.

See :ref:`corporate-proxies` for examples, including authentication and bypassing the proxy for internal hosts.

``HTTP_PROXY`` / ``http_proxy``
===============================

Proxy server for HTTP requests. Specify the proxy URL including protocol and port.

``HTTPS_PROXY`` / ``https_proxy``
=================================

Proxy server for HTTPS requests. Even though the proxy URL uses ``http://``, this handles HTTPS traffic.

``NO_PROXY`` / ``no_proxy``
===========================

Comma-separated list of hosts that should bypass the proxy. Use this for internal servers that don't require proxy
access.

***********************************
 SSL/TLS Certificate Configuration
***********************************

These variables configure SSL/TLS certificates for secure connections. Use them when your organization uses self-signed
certificates or custom certificate authorities.

``REQUESTS_CA_BUNDLE``
======================

Path to custom CA certificate bundle. The `requests <https://requests.readthedocs.io/>`_ library (which `pip
<https://pip.pypa.io/>`_ depends on) uses this variable. Alternative to ``PIP_CERT``.

See :ref:`corporate-certificates` for an example.

``SSL_CERT_FILE``
=================

Another variable for specifying a custom CA certificate bundle. Recognized by various Python libraries.

.. code-block:: console

    $ export SSL_CERT_FILE=/path/to/company-ca-bundle.crt
    $ python -m build

******************************
 Python Runtime Configuration
******************************

.. _python-warnings:

``PYTHONWARNINGS``
==================

Controls `Python's warning filters <https://docs.python.org/3/library/warnings.html>`_. Use this in CI to catch
deprecated features or potential issues in your build configuration by turning warnings into errors.

Catch deprecation warnings:

.. code-block:: console

    $ PYTHONWARNINGS=error::DeprecationWarning python -m build

Catch setuptools-specific warnings:

.. code-block:: console

    $ PYTHONWARNINGS=error:::setuptools.config.setupcfg python -m build

``PYTHONUTF8``
==============

Enables `UTF-8 mode <https://docs.python.org/3/library/os.html#utf-8-mode>`_ on Windows. Use this when building packages
with non-ASCII characters in filenames or file content on Windows systems.

.. code-block:: console

    $ set PYTHONUTF8=1
    $ python -m build

``TMPDIR`` / ``TEMP`` / ``TMP``
===============================

Controls where build creates the temporary isolated build environment. Useful for debugging or when you need the
temporary directory on a specific filesystem (e.g., for ccache or compilation caching).

On Unix-like systems, use ``TMPDIR``:

.. code-block:: console

    $ TMPDIR=/path/to/custom/tmp python -m build

On Windows, use ``TEMP``:

.. code-block:: console

    $ set TEMP=C:\path\to\custom\tmp
    $ python -m build

These variables only change *where* build creates the temporary directory. build still removes its environment when the
build ends. To pin the environment to a stable path, or to keep it for inspection, use the ``--env-dir`` option instead.

**Common use cases**:

- **Disk space**: Use a different filesystem with more available space
- **Performance**: Use faster storage (e.g., tmpfs on Linux)
- **Restricted filesystems**: Point at the writable part of a read-only container

``TMPDIR`` only relocates the base directory; build still appends a random suffix, so the extraction path differs on
every run. For compiler caches such as ``ccache`` or ``sccache``, which key on the source path, that random suffix is a
guaranteed cache miss - use ``--sdist-extract-dir`` to pin the path instead.

See :doc:`../how-to/troubleshooting` for debugging examples.

****************************
 Backend-Specific Variables
****************************

Each backend may define its own environment variables. See :ref:`backend-documentation` for links to backend guides.

*********************
 Non-Isolated Builds
*********************

When using ``--no-isolation``, build skips creating an `isolated environment
<https://packaging.python.org/en/latest/glossary/#term-Isolated-Build>`_. All environment variables from your current
shell pass directly to the build backend, including:

- ``PYTHONPATH`` - Affects Python module discovery
- ``PATH`` - Determines which executables are found
- Any custom variables your build backend uses

build does not set ``VIRTUAL_ENV`` in this mode. You're responsible for installing build dependencies yourself. See
:doc:`../how-to/basic-usage` for appropriate use cases.

**********************************
 Alternative: Configuration Files
**********************************

For persistent installer settings, see :ref:`pip-configuration`.

**********
 See also
**********

- :doc:`../how-to/corporate-environments` for proxy and SSL configuration
- :doc:`../how-to/troubleshooting` for common issues
- :doc:`cli` for command-line options
- `pip documentation <https://pip.pypa.io/en/stable/topics/configuration/>`_ for pip configuration
