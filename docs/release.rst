***************
Release Process
***************

You may release the project by following these steps:

#. Bump the version ``src/build/__init__.py``
#. Update ``CHANGELOG.rst`` with the new version and current date
#. Make a release commit with the changes made above
    - The commit message should follow the ``release X.Y.Z`` format
#. Make a signed tag (``git tag --sign X.Y.Z``)
    - The tag title should follow the ``build X.Y.Z`` format
    - The tag body should be a plaintext version of the changelog for the current
      release
#. Push the commit and tag to the repository (``git push`` and ``git push --tags``)
#. Make a release on GitHub or with the ``gh`` CLI tool. Copy the release notes
   into the release.

If you have any questions, please look at previous releases and/or ping the
other maintainers.
