########################
 Corporate Environments
########################

This guide covers common scenarios when using build behind corporate firewalls, with private package indexes (custom
package repositories), or in restricted network environments.

*************************
 Private package indexes
*************************

Using a private PyPI mirror
===========================

Set the ``PIP_INDEX_URL`` `environment variable
<https://pip.pypa.io/en/stable/topics/configuration/#environment-variables>`_ to point to your private `package index
<https://packaging.python.org/en/latest/glossary/#term-Package-Index>`_ (an alternative to `PyPI <https://pypi.org/>`_):

.. code-block:: console

    $ export PIP_INDEX_URL=https://pypi.company.com/simple
    $ python -m build

Or for a single command:

.. code-block:: console

    $ PIP_INDEX_URL=https://pypi.company.com/simple python -m build

Additional indexes
==================

To use both PyPI and a private index:

.. code-block:: console

    $ export PIP_INDEX_URL=https://pypi.org/simple
    $ export PIP_EXTRA_INDEX_URL=https://pypi.company.com/simple
    $ python -m build

.. warning::

    Using ``PIP_EXTRA_INDEX_URL`` has security implications. A malicious package on any index can shadow packages from
    other indexes. Use ``PIP_INDEX_URL`` exclusively when possible.

****************
 Authentication
****************

Embedded credentials
====================

You can embed credentials directly in the index URL:

.. code-block:: console

    $ PIP_INDEX_URL=https://username:password@pypi.company.com/simple python -m build

.. warning::

    Be careful with embedded credentials in shell history and CI logs. Use environment variable substitution when
    possible:

.. code-block:: console

    $ PIP_INDEX_URL=https://${PYPI_USER}:${PYPI_TOKEN}@pypi.company.com/simple python -m build

Using keyring
=============

Build passes ``--no-input`` to pip, preventing hidden credential prompts that cause the process to appear stuck. When
the ``keyring`` CLI is available on ``PATH``, build automatically sets ``PIP_KEYRING_PROVIDER=subprocess`` so pip
delegates credential lookups to the system keyring without needing keyring installed inside the isolated build
environment.

Install keyring system-wide so it is available on ``PATH``:

.. code-block:: console

    $ pipx install keyring

Or install build with the keyring extra:

.. code-block:: console

    $ pip install build[keyring]

Then store your credentials:

.. code-block:: console

    $ keyring set https://pypi.company.com username

For specialized backends (e.g., Google Artifact Registry, Azure Artifacts), install the corresponding keyring plugin
alongside keyring:

.. code-block:: console

    $ pipx install keyring
    $ pipx inject keyring keyrings.google-artifactregistry-auth

You can also set the keyring provider explicitly via environment variable, which is useful in CI or when keyring is
installed in a non-standard location:

.. code-block:: console

    $ export PIP_KEYRING_PROVIDER=subprocess
    $ python -m build

To disable keyring entirely:

.. code-block:: console

    $ export PIP_KEYRING_PROVIDER=disabled
    $ python -m build

Using .netrc
============

Create a ``~/.netrc`` file (``~/_netrc`` on Windows) with your credentials:

.. code-block:: text

    machine pypi.company.com
    login username
    password your-password

Ensure the file has restricted permissions:

.. code-block:: console

    $ chmod 600 ~/.netrc

**********************
 SSL/TLS certificates
**********************

Custom CA certificates
======================

If your company uses a custom CA certificate:

.. code-block:: console

    $ export REQUESTS_CA_BUNDLE=/path/to/company-ca-bundle.crt
    $ python -m build

Or use pip's certificate option:

.. code-block:: console

    $ export PIP_CERT=/path/to/company-ca-bundle.crt
    $ python -m build

Self-signed certificates
========================

For development environments with self-signed certificates (not recommended for production):

.. code-block:: console

    $ export PIP_TRUSTED_HOST=pypi.company.com
    $ python -m build

Using virtualenv for better SSL support
=======================================

If you encounter SSL/TLS errors with Python's built-in venv, install virtualenv:

.. code-block:: console

    $ pip install build[virtualenv]

This provides a more recent version of pip with better SSL support and truststore capabilities.

.. note::

    Python 3.11.8+ and 3.12.2+ have improved SSL support and may not need this workaround.

***************
 Proxy servers
***************

HTTP/HTTPS proxies
==================

Configure proxy environment variables:

.. code-block:: console

    $ export HTTP_PROXY=http://proxy.company.com:8080
    $ export HTTPS_PROXY=http://proxy.company.com:8080
    $ python -m build

With authentication:

.. code-block:: console

    $ export HTTP_PROXY=http://user:pass@proxy.company.com:8080
    $ export HTTPS_PROXY=http://user:pass@proxy.company.com:8080

No proxy for certain hosts
==========================

.. code-block:: console

    $ export NO_PROXY=localhost,127.0.0.1,.company.com
    $ python -m build

*************************
 pip configuration files
*************************

Global configuration
====================

Instead of environment variables, you can create a pip configuration file.

On Linux/macOS (``~/.config/pip/pip.conf``):

.. code-block:: ini

    [global]
    index-url = https://pypi.company.com/simple
    trusted-host = pypi.company.com
    cert = /path/to/company-ca-bundle.crt

On Windows (``%APPDATA%\\pip\\pip.ini``):

.. code-block:: ini

    [global]
    index-url = https://pypi.company.com/simple
    trusted-host = pypi.company.com
    cert = C:\\path\\to\\company-ca-bundle.crt

Per-project configuration
=========================

Create a ``pip.conf`` file in your project directory. This is useful for team settings.

*************************
 Air-gapped environments
*************************

For completely offline builds, you must manually install dependencies first:

.. code-block:: console

    $ pip install setuptools wheel your-build-backend
    $ python -m build --no-isolation

The ``--no-isolation`` flag tells build to use your current environment instead of creating an isolated one.

.. warning::

    When using ``--no-isolation``, ensure all build dependencies are installed and compatible.

********************
 CI/CD environments
********************

GitHub Actions
==============

.. code-block:: yaml

    - name: Build package
      run: python -m build
      env:
        PIP_INDEX_URL: ${{ secrets.PYPI_INDEX_URL }}
        PIP_CERT: /path/to/cert.crt

GitLab CI
=========

.. code-block:: yaml

    build:
      script:
        - export PIP_INDEX_URL=$PYPI_INDEX_URL
        - python -m build

***************************
 Catching backend warnings
***************************

To catch deprecation warnings from your build backend (useful in CI):

.. code-block:: console

    $ PYTHONWARNINGS=error::DeprecationWarning python -m build

Or for setuptools specifically:

.. code-block:: console

    $ PYTHONWARNINGS=error:::setuptools.config.setupcfg python -m build

See :doc:`troubleshooting` for more details on warnings.

***************
 Common issues
***************

Build fails with authentication errors
======================================

Build passes ``--no-input`` to pip to prevent hidden credential prompts. If your private index requires authentication,
pip will fail instead of hanging. Configure one of the authentication methods above (embedded credentials, keyring, or
``.netrc``) to provide credentials non-interactively.

401/403 errors
==============

Authentication failed. Verify your credentials and ensure they have access to the required packages.

SSL verification failed
=======================

Your system doesn't trust the certificate. Use ``REQUESTS_CA_BUNDLE`` or ``PIP_CERT`` to provide the CA certificate, or
install ``build[virtualenv]`` for better SSL support.

Conda environment conflicts
===========================

If you're in a conda environment and experiencing venv creation issues:

.. code-block:: console

    $ conda deactivate
    $ python -m build

Or use virtualenv:

.. code-block:: console

    $ pip install build[virtualenv]
    $ python -m build

**********
 See also
**********

- :doc:`troubleshooting` for more problem-solving tips
- :doc:`../reference/environment-variables` for a complete list of environment variables
- `pip documentation <https://pip.pypa.io/>`_ for more pip configuration options
