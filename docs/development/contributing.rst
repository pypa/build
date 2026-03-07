##############
 Contributing
##############

build welcomes contributions from the community. This guide explains how to contribute to the project.

*******************
 Development Setup
*******************

To contribute to build, you need a development environment set up on your local machine. Start by forking the
`repository on GitHub <https://github.com/pypa/build>`_ and cloning your fork to your local machine. Once cloned,
navigate to the project directory and install build in development mode along with all development dependencies.

The project uses `tox <https://tox.wiki/>`_ for managing development environments and running tests. Install tox
globally or in a virtual environment, then use it to run tests and other development tasks. The tox configuration
includes environments for testing across multiple Python versions, running linters, building documentation, and more.

**********************
 Development Workflow
**********************

The typical development workflow begins with creating a new branch for your changes. Branch names should be descriptive
of the feature or fix you're implementing. Make your changes in this branch, ensuring you add or update tests to cover
your modifications.

Before committing, run the test suite locally to verify your changes don't break existing functionality. The project
uses `pytest <https://docs.pytest.org/>`_ for testing, and you can run tests using tox. After ensuring tests pass,
commit your changes with a clear, descriptive commit message following the project's commit conventions.

When your changes are ready, push your branch to your fork on GitHub and open a pull request against the main build
repository. The pull request description should clearly explain what changes you've made and why. Reference any related
issues using GitHub's issue linking syntax.

***************
 Running Tests
***************

Due to its nature, build has a somewhat complex test suite with two sets of tests: unit tests and integration tests.
Unit tests verify the actual code implementation, while integration tests run build on real world projects as a sanity
check. Integration tests take a long time to run and are not very helpful for tracking down issues, so they are disabled
by default. They can be enabled by passing either ``--run-integration`` or ``--only-integration`` arguments to pytest,
where the latter will disable unit tests and only run integration tests. Even though these tests are disabled by
default, they will be run in CI where test suite run durations are not a big issue.

To run the test suite, use tox which automates running tests on different environments. Simply run ``tox`` in the
project directory to execute the full test suite. The project has a fairly large environment matrix, running tests for
all supported Python versions and implementations, and with the module being invoked directly from path, sdist install,
or wheel install. Additionally, there are environments for type checking and documentation building, plus extras like
checking code with minimum versions of dependencies.

Some example commands for this project include running type checking with ``tox -e type``, running only unit tests
against Python 3.9 with ``tox -e py39``, running both unit and integration tests with ``tox -- --run-integration``,
running only integration tests with ``tox -- --only-integration``, or running only integration tests with parallel tasks
using ``tox -- -n auto --only-integration``. You can also run unit tests against a specific Python version with wheel
installation using ``tox -e py39-wheel``.

Code coverage is tracked to ensure all code paths are tested. Aim for complete coverage of any new code you add. The CI
system will report coverage metrics on your pull request and runs the test suite across all supported operating systems.

************************
 Code Style and Linting
************************

build follows modern Python code style conventions enforced by `ruff <https://docs.astral.sh/ruff/>`_. Before submitting
a pull request, run the linter to ensure your code meets the project's style guidelines. The ruff configuration is
defined in the pyproject.toml file and includes both formatting and linting rules.

The project also uses type annotations throughout the codebase. All new code should include appropriate type hints, and
changes to existing code should preserve or improve type annotations. Use `pyright
<https://microsoft.github.io/pyright/>`_ for type checking to verify your type annotations are correct.

***************
 Documentation
***************

Good documentation is essential for build's users and contributors. If your contribution adds new features or changes
existing behavior, update the relevant documentation files. The documentation is written in `reStructuredText
<https://docutils.sourceforge.io/rst.html>`_ and built using `Sphinx <https://www.sphinx-doc.org/>`_.

The documentation follows the `Diataxis framework <https://diataxis.fr/>`_, organizing content into tutorials, how-to
guides, technical reference, and explanations. Place your documentation in the appropriate section based on its purpose.
Tutorial content teaches beginners, how-to guides solve specific problems, reference sections document details, and
explanations provide context and design rationale.

Build the documentation locally to verify your changes render correctly. The tox configuration includes an environment
for building docs. Review the rendered output to ensure formatting, links, and code examples appear as intended.

**********************
 Pull Request Process
**********************

When you open a pull request, maintainers will review your changes and may request modifications. Be responsive to
feedback and make requested changes in additional commits on your branch. The pull request will be merged once approved
by a maintainer and all CI checks pass.

The CI system runs the full test suite across all supported Python versions, verifies code style compliance, builds the
documentation, and performs other checks. All CI checks must pass before a pull request can be merged. If CI fails,
review the output to understand what went wrong and push fixes to your branch.

****************
 Issue Tracking
****************

Before starting work on a significant feature or change, check the issue tracker to see if it's already been discussed.
If not, consider opening an issue to discuss your proposed changes with maintainers. This helps ensure your contribution
aligns with the project's direction and avoids duplicate effort.

When reporting bugs, include detailed information about the issue. Provide the full error message and traceback,
describe what you expected to happen versus what actually happened, list the steps to reproduce the problem, and include
information about your environment such as Python version and operating system.

For feature requests, explain the use case and why the feature would benefit build's users. Include examples of how the
feature would be used if implemented.

*****************
 Release Process
*****************

build uses a structured release process managed by maintainers. Releases follow `semantic versioning
<https://semver.org/>`_, with version numbers indicating the level of changes. The changelog documents all changes in
each release, organized by type such as features, bug fixes, and deprecations.

As a contributor, you don't need to worry about creating releases, but understanding the process can help you write
better changelog entries and commit messages. Maintainers release the project by first bumping the version in
``src/build/__init__.py`` and updating ``CHANGELOG.rst`` with the new version and current date. They then make a release
commit with these changes using the format ``release X.Y.Z`` for the commit message. Next, they create a signed tag with
``git tag --sign X.Y.Z`` where the tag title follows the ``build X.Y.Z`` format and the tag body contains a plaintext
version of the changelog for the current release. Finally, they push both the commit and tag to the repository using
``git push`` and ``git push --tags``, then make a release on GitHub or with the gh CLI tool, copying the release notes
into the release. If you have questions about the release process, look at previous releases or reach out to other
maintainers.

**********************
 Community Guidelines
**********************

build is part of the `PyPA (Python Packaging Authority) <https://www.pypa.io/>`_ ecosystem and follows the PyPA Code of
Conduct. Be respectful and constructive in all interactions with other contributors. Focus feedback on the code and
ideas, not on individuals.

The project values clear communication, thorough testing, and well-documented code. Take time to explain your changes
clearly in commit messages and pull requests. Write tests that future contributors can understand. Document not just
what your code does, but why you made particular design choices.

**************
 Getting Help
**************

If you have questions about contributing, several resources are available. The issue tracker can be used for questions,
though complex discussions may be better suited to other venues. The project's documentation includes extensive
information about build's design and implementation.

For real-time discussion, consider joining the `PyPA Discord server <https://discord.gg/pypa>`_ where many packaging
tool maintainers and contributors participate. You can also ask questions on the `Python Packaging Discourse forum
<https://discuss.python.org/c/packaging/14>`_.

**********
 See also
**********

- `PyPA Code of Conduct <https://www.pypa.io/en/latest/code-of-conduct/>`_
- `Issue Tracker <https://github.com/pypa/build/issues>`_
- `tox documentation <https://tox.wiki/>`_
- `pytest documentation <https://docs.pytest.org/>`_
- `ruff documentation <https://docs.astral.sh/ruff/>`_
- `Sphinx documentation <https://www.sphinx-doc.org/>`_
- `PyPA Discord <https://discord.gg/pypa>`_
- `Python Packaging Discourse <https://discuss.python.org/c/packaging/14>`_
