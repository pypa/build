=========
CLI Usage
=========

.. autoprogram:: build.__main__:main_parser()
   :prog: python -m build

.. note::

   A ``pyproject-build`` CLI script is also available, so that tools such as pipx_
   can use it.

By default build will build the package in an isolated
environment, but this behavior can be disabled with `--no-isolation`.

.. _pipx: https://github.com/pipxproject/pipx
