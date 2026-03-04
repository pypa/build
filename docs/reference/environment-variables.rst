#######################
 Environment Variables
#######################

This reference documents environment variables that affect build's behavior. You can use these to configure private
package indexes, proxies, SSL certificates, and other settings.

************************
 Variables Set by build
************************

``VIRTUAL_ENV``
===============

build sets this variable when creating `isolated environments
<https://packaging.python.org/en/latest/glossary/#term-Isolated-Build>`_. It contains the absolute path to the temporary
`virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ that build creates for installing dependencies.
Build backends can use this to detect they're running in an isolated environment.

*****************************
 Package Index Configuration
*****************************

build uses `pip <https://pip.pypa.io/>`_ to install build dependencies in isolated environments. Configure pip using
these environment variables to work with private package indexes or mirrors. For detailed examples, see
:doc:`../how-to/corporate-environments`.

``PIP_INDEX_URL``
=================

Sets the primary `package index <https://packaging.python.org/en/latest/glossary/#term-Package-Index>`_ URL where pip
looks for packages. Use this to point to private package repositories or PyPI mirrors. Defaults to
``https://pypi.org/simple``.

.. code-block:: console

    $ export PIP_INDEX_URL=https://pypi.company.com/simple
    $ python -m build

``PIP_EXTRA_INDEX_URL``
=======================

Adds additional package indexes to search beyond the primary index. This allows using both `PyPI <https://pypi.org/>`_
and a private index simultaneously.

.. code-block:: console

    $ export PIP_EXTRA_INDEX_URL=https://pypi.company.com/simple
    $ python -m build

.. warning::

    A malicious package on any extra index can shadow packages from other indexes. Use ``PIP_INDEX_URL`` exclusively
    when possible for better security.

``PIP_CERT``
============

Path to a custom CA certificate bundle for SSL/TLS verification. Use this when your organization uses self-signed
certificates or a custom certificate authority. Defaults to system certificates.

.. code-block:: console

    $ export PIP_CERT=/path/to/company-ca-bundle.crt
    $ python -m build

``PIP_TRUSTED_HOST``
====================

Disables SSL verification for the specified host. Only use this in secure development environments where SSL
certificates aren't available.

.. code-block:: console

    $ export PIP_TRUSTED_HOST=pypi.company.com
    $ python -m build

.. warning::

    Disabling SSL verification is insecure. Prefer using ``PIP_CERT`` with proper certificates.

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

``HTTP_PROXY`` / ``http_proxy``
===============================

Proxy server for HTTP requests. Specify the proxy URL including protocol and port.

.. code-block:: console

    $ export HTTP_PROXY=http://proxy.company.com:8080
    $ python -m build

``HTTPS_PROXY`` / ``https_proxy``
=================================

Proxy server for HTTPS requests. Even though the proxy URL uses ``http://``, this handles HTTPS traffic.

.. code-block:: console

    $ export HTTPS_PROXY=http://proxy.company.com:8080
    $ python -m build

``NO_PROXY`` / ``no_proxy``
===========================

Comma-separated list of hosts that should bypass the proxy. Use this for internal servers that don't require proxy
access.

.. code-block:: console

    $ export NO_PROXY=localhost,127.0.0.1,.company.com
    $ python -m build

***********************************
 SSL/TLS Certificate Configuration
***********************************

These variables configure SSL/TLS certificates for secure connections. Use them when your organization uses self-signed
certificates or custom certificate authorities.

``REQUESTS_CA_BUNDLE``
======================

Path to custom CA certificate bundle. The `requests <https://requests.readthedocs.io/>`_ library (which `pip
<https://pip.pypa.io/>`_ depends on) uses this variable. Alternative to ``PIP_CERT``.

.. code-block:: console

    $ export REQUESTS_CA_BUNDLE=/path/to/company-ca-bundle.crt
    $ python -m build

``SSL_CERT_FILE``
=================

Another variable for specifying a custom CA certificate bundle. Recognized by various Python libraries.

.. code-block:: console

    $ export SSL_CERT_FILE=/path/to/company-ca-bundle.crt
    $ python -m build

******************************
 Python Runtime Configuration
******************************

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

The temporary directory persists after build completes, allowing you to inspect build artifacts, logs, and the isolated
environment for debugging. By default, build uses the system's default temporary directory and cleans it up after the
build.

**Common use cases**:

- **Debugging**: Keep temp directory to inspect build logs
- **ccache**: Place builds on a filesystem where ccache can cache compilation
- **Disk space**: Use a different filesystem with more available space
- **Performance**: Use faster storage (e.g., tmpfs on Linux)

See :doc:`../how-to/troubleshooting` for debugging examples.

****************************
 Backend-Specific Variables
****************************

Each **build backend** may define its own environment variables for configuration. Check your backend's documentation:

- `Setuptools <https://setuptools.pypa.io/en/latest/userguide/index.html>`_
- `Hatchling <https://hatch.pypa.io/latest/config/build/>`_
- `PDM-Backend <https://pdm-backend.fming.dev/>`_
- `Flit <https://flit.pypa.io/en/stable/>`_
- `Poetry-Core <https://python-poetry.org/docs/pyproject/>`_
- `scikit-build-core <https://scikit-build-core.readthedocs.io/en/latest/configuration.html>`_
- `meson-python <https://meson-python.readthedocs.io/en/latest/reference/config-settings.html>`_

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

Instead of environment variables, you can configure `pip <https://pip.pypa.io/>`_ using persistent configuration files.
This is convenient if you always use the same settings.

**Linux/macOS**: ``~/.config/pip/pip.conf``

**Windows**: ``%APPDATA%\\pip\\pip.ini``

Example configuration:

.. code-block:: ini

    [global]
    index-url = https://pypi.company.com/simple
    trusted-host = pypi.company.com
    cert = /path/to/company-ca-bundle.crt

For more details and examples, see :doc:`../how-to/corporate-environments` and the `pip configuration documentation
<https://pip.pypa.io/en/stable/topics/configuration/>`_.

**********
 See also
**********

- :doc:`../how-to/corporate-environments` for proxy and SSL configuration
- :doc:`../how-to/troubleshooting` for common issues
- :doc:`cli` for command-line options
- `pip documentation <https://pip.pypa.io/en/stable/topics/configuration/>`_ for pip configuration
