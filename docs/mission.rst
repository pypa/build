=================
Mission Statement
=================

In the Python ecosystem, the build system tools and the package management
are very intertwined. While it might be useful for user to be able to access
all this capabilities in a single project (such as pip_), there are several
use cases where this is not desirable. The main being custom environments
(outside PyPI_) or situations where the user does its own package management,
such as Linux distributions.

This project aims to fit the "building packages hole" for such use-cases in
:pep:`517`/:pep:`518` workflows.

As it is intended to be used by users that do their own package management,
we will try to keep dependencies to a minimum, in order to try make
bootstrapping easier.

.. _pip: https://github.com/pypa/pip
.. _PyPI: https://pypi.org/
