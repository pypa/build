#########
 Release
#########

Releases follow `semantic versioning <https://semver.org/>`_ and use automated workflows to handle version bumping,
changelog building, commit creation, and publishing. Maintainers trigger releases through GitHub Actions or run the
release script locally for testing.

*********************
 Changelog Fragments
*********************

Contributors add changelog fragments that get collected during releases. Create a file in ``docs/changelog/`` named
``<pr_number>.<type>.rst`` where type is ``feature`` for new functionality, ``bugfix`` for fixes, ``doc`` for
documentation changes, ``removal`` for deprecations, or ``misc`` for internal changes. The file should contain a single
line describing the change, optionally crediting the author with ``:user:`username``` syntax. For example,
``123.feature.rst`` might contain ``Add support for custom backends - by :user:`contributor```. These fragments are
collected during releases to build the changelog automatically.

*******************
 Automated Release
*******************

Navigate to the `pre-release workflow <https://github.com/pypa/build/actions/workflows/pre-release.yml>`_ and click Run
workflow. Select a version bump type: ``auto`` for patch bumps, ``major`` for X+1.0.0, ``minor`` for X.Y+1.0, or
``patch`` for X.Y.Z+1.

The workflow updates the version in ``src/build/__init__.py``, runs ``towncrier build`` to collect changelog fragments
from ``docs/changelog/`` and incorporate them into ``CHANGELOG.rst``, creates a release commit with message ``chore:
prepare for X.Y.Z``, creates an annotated tag, and pushes both to trigger the CD workflow.

The tag push triggers the continuous deployment pipeline which builds the source distribution and wheel, creates a
GitHub release with auto-generated notes, generates build attestations for supply chain security, and publishes to PyPI
via trusted publishing. The process takes approximately five minutes from workflow trigger to published package.

***************
 Local Release
***************

Run the release script locally for testing or manual control. Ensure tox is installed and git identity is configured:

.. code-block:: console

    $ pip install tox
    $ git config user.name "Your Name"
    $ git config user.email "your@email.com"

The script creates annotated git tags without GPG signing. Package authenticity is guaranteed by PyPI attestations, not
git tag signatures.

Dry run without pushing
=======================

Test the release process locally:

.. code-block:: console

    $ tox -e release -- --version auto --no-push

This updates the version file, builds the changelog from fragments, creates the commit and tag locally, but does not
push to the remote repository.

Full local release
==================

Specify an explicit version or bump type:

.. code-block:: console

    $ tox -e release -- --version 1.5.0
    $ tox -e release -- --version patch  # 1.4.0 → 1.4.1
    $ tox -e release -- --version minor  # 1.4.0 → 1.5.0
    $ tox -e release -- --version major  # 1.4.0 → 2.0.0

The script updates ``src/build/__init__.py``, runs ``towncrier build`` to collect changelog fragments, runs pre-commit
hooks, creates a commit with message ``chore: prepare for X.Y.Z``, creates an annotated tag, and pushes both to origin.
The GitHub Actions CD workflow takes over to build and publish.

**********
 See also
**********

PyPI removed PGP signature support in May 2023. Package authenticity is guaranteed through PyPI attestations per PEP
740, which cryptographically link packages to their source repository and build process.

*****************
 Troubleshooting
*****************

Workflow timeout
================

If the pre-release workflow times out, run the release script locally with ``--no-push``, then manually push with ``git
push && git push --tags``. The CD workflow triggers automatically on tag push.

Publishing conflicts
====================

If a version is already published to PyPI, the publish job fails safely. The CD workflow is idempotent except for PyPI
publishing. For corrections, create a post-release like ``X.Y.Z.post1``.

****************
 Implementation
****************

The automation consists of the pre-release workflow at ``.github/workflows/pre-release.yml`` for manual triggering, the
CD workflow at ``.github/workflows/cd.yml`` that triggers on tag pushes, the release script at ``tasks/release.py`` for
version bumping and tag creation, and the ``[testenv:release]`` environment in ``tox.ini`` providing dependencies.
