#####################
 Changelog Fragments
#####################

This directory contains changelog fragments for the next release. Each PR should include a fragment file describing the
change.

********************
 Creating Fragments
********************

Create a file named ``<pr_number>.<type>.rst`` where type is one of:

- ``feature`` - new functionality
- ``bugfix`` - bug fix
- ``doc`` - documentation improvement
- ``removal`` - deprecation or removal
- ``misc`` - internal change (not user-visible)

Example: ``991.feature.rst``

Content should be a single line describing the change:

::

    Add support for custom build backends - by :user:`yourname`

Use ``:issue:`123``` to reference issues and ``:user:`name``` for attribution.

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
