#####################
 Changelog Fragments
#####################

This directory contains changelog fragments for the next release. Each PR should include a fragment file describing the
change.

********************
 Creating Fragments
********************

Create a file named ``<pr_number>.<type>.rst`` where type is one of:

- ``feature`` - new functionality (minor bump)
- ``bugfix`` - bug fix (patch bump)
- ``doc`` - documentation improvement (patch bump)
- ``deprecation`` - something still works but warns it will go away (minor bump)
- ``removal`` - something callers relied on is gone; breaking (major bump)
- ``misc`` - internal change, not user-visible (patch bump)

The type drives the ``auto`` release bump, so pick ``removal`` only for a genuine break and ``deprecation`` for a
warning that keeps working.

Example: ``991.feature.rst``

Content should be a single line describing the change:

::

    Add support for custom build backends - by :user:`yourname`

Use ``:issue:`123``` to reference issues and ``:user:`name``` for attribution. Write one line; the release reflows the
built ``CHANGELOG.rst`` with ``docstrfmt`` at 120 columns, so wrapping is not something you manage in the fragment.

*****************
 Preview Changes
*****************

See what the changelog will look like:

::

    towncrier build --draft --version X.Y.Z

*****************
 Build Changelog
*****************

Maintainers build the changelog during releases:

::

    towncrier build --yes --version X.Y.Z

This collects all fragments, adds them to CHANGELOG.rst, and deletes the fragment files.
