**********
Test Suite
**********

Due to its nature, ``build`` has a somewhat complex test suite, which we will
try to go through in this document.

Firstly, there are two set of tests, unit tests and integration tests. In unit
tests, we test the actual code implementation. In integration tests, we test
``build`` on a few real world projects; this is mostly a sanity test.

Integration tests take a long time to run, and are not very helpful tracking
down issues, so they are **disabled by default**. They can be enabled by passing
either ``--run-integration`` or ``--only-integration`` arguments to pytest,
where the latter will disable the unit tests and only run the integration ones.
Even though these tests are disabled by default, they will be run in CI,
where test suite run durations are not a big issue.

To run the test suite we use ``tox``, which automates running the test suite on
different environments:


.. code-block:: console

     tox


You can find out more about how to run ``tox`` and its arguments in the
`tox documentation`_.

We have a fairly large environment matrix. We run tests for all supported Python
versions and implementations, and with the module being invoked from path,
sdist install, or wheel install. Additionally, we have an environment for type
checking, and one to produce the documentation. There are some other extra
environments, like checking the code with the minimum version of each
dependency.

Some examples commands for this project:
  - Run type checking: ``tox -e type``
  - Only run unit tests against Python 3.9: ``tox -e py39``
  - Run both unit and integration tests: ``tox -- --run-integration``
  - Only run integration tests: ``tox -- --only-integration``
  - Only run integration tests with parallel tasks: ``tox -- -n auto --only-integration``
  - Only run unit tests against Python 3.9 with the module installed via wheel: ``tox -e py39-wheel``


We have CI testing, where we the test suite across all supported operating
systems, and have test coverage reports.


.. _tox documentation: https://tox.readthedocs.io/
