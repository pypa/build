============================
Differences from other tools
============================

``pep517.build``
----------------

build implements a CLI tailored to end users.

``pep517.build`` contained a proof-of-concept of a :pep:`517`
frontend. It *"implement[ed] essentially the simplest possible frontend
tool, to exercise and illustrate how the core functionality can be
used"*. It has since been `deprecated and is scheduled for removal`_.

``setup.py sdist bdist_wheel``
------------------------------

build is roughly the equivalent of ``setup.py sdist bdist_wheel`` but
with :pep:`517` support, allowing use with projects that don't use setuptools.

.. _deprecated and is scheduled for removal: https://github.com/pypa/pep517/pull/83

Custom Behaviors
----------------

Fallback Backend
^^^^^^^^^^^^^^^^

As recommended in :pep:`517`, if no backend is specified, ``build`` will
fallback to ``setuptools.build_meta:__legacy__``.
