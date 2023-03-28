***************
Release Process
***************

As this project is critical to the Python ecosystem's supply chain security, all
releases are PGP signed with one of the keys listed in the :doc:`installation page <installation>`.
Before releasing please make sure your PGP key is listed there, and preferably
signed by one of the other key holders. If your key is not signed by one of the
other key holders, please make sure the PR that added your key to the
:doc:`installation page <installation>` was approved by at least one other maintainer.

After that is done, you may release the project by following these steps:

#. Bump the versions in ``pyproject.toml`` and ``src/build/__init__.py``
#. Update ``CHANGELOG.rst`` with the new version and current date
#. Make a release commit with the changes made above
    - The commit message should follow the ``release X.Y.Z`` format
#. Make a signed tag (``git tag -s X.Y.Z``)
    - The tag title should follow the ``build X.Y.Z`` format
    - The tag body should be a plaintext version of the changelog for the current
      release
#. Push the commit and tag to the repository (``git push`` and ``git push --tags``)
#. Build the Python artifacts (``python -m build``)
#. Sign and push the artifacts to PyPI (``twine upload -s dist/*``)

If you have any questions, please look at previous releases and/or ping the
other maintainers.
