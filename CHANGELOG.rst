+++++++++
Changelog
+++++++++

1.4.0 (2026-01-08)
==================

- Add ``--quiet`` flag
  (:pr:`947`)
- Add option to dump PEP 517 metadata with ``--metadata``
  (:pr:`940`, :pr:`943`)
- Support ``UV`` environment variable
  (:pr:`971`)
- Remove a workaround for 3.14b1
  (:pr:`960`)
- In 3.14 final release, ``color`` defaults to ``True`` already
  (:pr:`962`)
- Pass sp-repo-review
  (:pr:`942`)
- In pytest configuration, ``log_level`` is better than ``log_cli_level``
  (:pr:`950`)
- Split up typing and mypy
  (:pr:`944`)
- Use ``types-colorama``
  (:pr:`945`)
- In docs, first argument for ``_has_dependency`` is a name
  (PR :pr:`970`)
- Fix test failure when ``flit-core`` is installed
  (PR :pr:`921`)


1.3.0 (2025-08-01)
==================

- Add ``--config-json``
  (PR :pr:`916`, fixes issue :issue:`900`)
- Drop Python 3.8
  (PR :pr:`891`)
- Test on Python 3.14, colorful help on 3.14+
  (PR :pr:`895`)
- Fix ``ModuleNotFoundError`` when ``pip`` is not installed
  (PR :pr:`898`)
- Disable use of ``pip install --python`` for debundled pip
  (PR :pr:`861`)
- Don't pass no-wheel to virtualenv if it would warn
  (PR :pr:`892`)
- Optimize our tests to run faster
  (PR :pr:`871`, :pr:`872`, :pr:`738`)
- Allow running our tests without virtualenv
  (PR :pr:`911`)
- Fix issues in our tests
  (PR :pr:`824`, :pr:`918`, :pr:`870`, :pr:`915`, :pr:`862`, :pr:`863`, :pr:`899`, :pr:`896`, :pr:`854`)
- Use SPDX identifiers for our license metadata
  (PR :pr:`914`)
- Use dependency-groups for our development
  (PR :pr:`880`)
- Mention conda and update uv mention in README/docs
  (PR :pr:`842`, :pr:`816`, :pr:`917`)

1.2.2 (2024-09-06)
==================

- Add editable to ``builder.get_requries_for_build``'s static types
  (PR :pr:`764`, fixes issue :issue:`763`)
- Include artifact attestations in our release
  (PR :pr:`782`)
- Fix typing compatibility with typed ``pyproject-hooks``
  (PR :pr:`788`)
- Mark more tests with ``network``
  (PR :pr:`808`)
- Add more intersphinx links to docs
  (PR :pr:`804`)
- Make ``uv`` optional for tests
  (PR :pr:`807` and :pr:`813`)

1.2.1 (2024-03-28)
==================

- Avoid error when terminal width is undetectable on Python < 3.11
  (PR :pr:`761`)

1.2.0 (2024-03-27)
==================

- Add ``--installer`` option, supporting ``pip`` and ``uv``. Added ``uv``
  extra.
  (PR :pr:`751`)
- Improve console output and provide ``-v`` for dependency installation
  (PR :pr:`749`)
- Avoid compiling unused bytecode when using ``pip``
  (PR :pr:`752`)
- Dropped support for Python 3.7
  (PR :pr:`743`)


1.1.1 (2024-02-29)
==================

- Fixed invoking outer pip from user site packages
  (PR :pr:`746`, fixes issue :issue:`745`)
- Corrected the minimum pip version required to use an outer pip
  (PR :pr:`746`, fixes issue :issue:`745`)


1.1.0 (2024-02-29)
==================

- Use external pip if available instead of installing, speeds up environment
  setup with virtualenv slightly and venv significantly.
  (PR :pr:`736`)
- Stopped injecting ``wheel`` as a build dependency automatically, in the
  case of missing ``pyproject.toml`` -- by :user:`webknjaz`.
  (PR :pr:`716`)
- Use ``importlib_metadata`` on Python <3.10.2 for bugfixes not present in
  those CPython standard libraries (not required when bootstrapping) -- by
  :user:`GianlucaFicarelli`.
  (PR :pr:`693`, fixes issue :issue:`692`)


1.0.3 (2023-09-06)
==================

- Avoid CPython 3.8.17, 3.9.17, 3.10.12, and 3.11.4 tarfile symlink bug
  triggered by adding ``data_filter`` in 1.0.0.
  (PR :pr:`675`, fixes issue :issue:`674`)


1.0.0 (2023-09-01)
==================

- Removed the ``toml`` library fallback; ``toml`` can no longer be used
  as a substitute for ``tomli``
  (PR :pr:`567`)
- Added ``runner`` parameter to ``util.project_wheel_metadata``
  (PR :pr:`566`, fixes issue :issue:`553`)
- Modified ``ProjectBuilder`` constructor signature, added alternative
  ``ProjectBuilder.from_env`` constructor, redefined ``env.IsolatedEnv``
  interface, and exposed ``env.DefaultIsolatedEnv``, replacing
  ``env.IsolatedEnvBuilder``.  The aim has been to shift responsibility for
  modifying the environment from the project builder to the ``IsolatedEnv``
  entirely and to ensure that the builder will be initialised from an
  ``IsolatedEnv`` in a consistent manner.  Mutating the project builder is no
  longer supported.
  (PR :pr:`537`)
- ``virtualenv`` is no longer imported when using ``-n``, for faster builds
  (PR :pr:`636`, fixes issue :issue:`510`)
- The SDist now contains the repository contents, including tests. Flit-core
  3.8+ required.
  (PR :pr:`657`, :pr:`661`, fixes issue :issue:`656`)
- The minimum version of ``importlib-metadata`` has been increased to 4.6 and
  Python 3.10 due to a bug in the standard library version with URL
  requirements in extras. This is still not required for 3.8 when bootstrapping
  (as long as you don't have URL requirements in extras).
  (PR :pr:`631`, fixes issue :issue:`630`)
- Docs now built with Sphinx 7
  (PR :pr:`660`)
- Tests now contain a ``network`` marker
  (PR :pr:`649`, fixes issue :issue:`648`)
- Config-settings are now passed to ``get_requires*`` hooks, fixing a long
  standing bug. If this affects your setuptools build, you can use
  ``-C--build-option=<cmd> -C--build-option=<option>`` to workaround an issue
  with Setuptools not allowing unrecognised build options when running this
  hook.
  (PR :pr:`627`, fixes issue :issue:`#264`)
- Test on Python 3.12 betas/RCs
  (PR :pr:`624`)
- Filter out malicious files when extracting tar archives when Python supports it
  (PR :pr:`609`)
- Specify encoding, fixing issues when ``PYTHONWARNDEFAULTENCODING`` is set.
  (PR :pr:`587`, fixes issue :issue:`577`)
- Ruff is now used for linting.


0.10.0 (2023-01-11)
===================

- Replace ``pep517`` dependency with ``pyproject_hooks``,
  into which ``pep517`` has been renamed
  (PR :pr:`539`, Fixes :issue:`529`)
- Change build backend from ``setuptools`` to ``flit``
  (PR :pr:`470`, Fixes :issue:`394`)
- Dropped support for Python 3.6 (PR :pr:`532`)



0.9.0 (2022-10-27)
==================

- Hide a Python 3.11.0 unavoidable warning with venv (PR :pr:`527`)
- Fix infinite recursion error in ``check_dependency`` with circular
  dependencies (PR :pr:`512`, Fixes :issue:`511`)
- Only import colorama on Windows (PR :pr:`494`, Fixes :issue:`493`)
- Flush output more often to reduce interleaved output (PR :pr:`494`)
- Small API cleanup, like better ``_all__`` and srcdir being read only. (PR :pr:`477`)
- Only use ``importlib_metadata`` when needed (PR :pr:`401`)
- Clarify in printout when build dependencies are being installed (PR :pr:`514`)



0.8.0 (2022-05-22)
==================

- Accept ``os.PathLike[str]`` in addition to ``str`` for paths in public
  API (PR :pr:`392`, Fixes :issue:`372`)
- Add schema validation for ``build-system`` table to check conformity
  with PEP 517 and PEP 518 (PR :pr:`365`, Fixes :issue:`364`)
- Better support for Python 3.11 (sysconfig schemes PR :pr:`434`,  PR :pr:`463`, tomllib PR :pr:`443`, warnings PR :pr:`420`)
- Improved error printouts (PR :pr:`442`)
- Avoid importing packaging unless needed (PR :pr:`395`, Fixes :issue:`393`)

Breaking Changes
----------------

- Failure to create a virtual environment in the ``build.env`` module now raises
  ``build.FailedProcessError`` (PR :pr:`442`)



0.7.0 (2021-09-16)
==================

- Add ``build.util`` module with an high-level utility API (PR :pr:`340`)



0.6.0.post1 (2021-08-05)
========================

- Fix compatibility with Python 3.6 and 3.7 (PR :pr:`339`, Fixes :issue:`338`)



0.6.0 (2021-08-02)
==================

- Improved output (PR :pr:`333`, Fixes :issue:`142`)
- The CLI now honors ``NO_COLOR`` (PR :pr:`333`)
- The CLI can now be forced to colorize the output by setting the ``FORCE_COLOR`` environment variable (PR :pr:`335`)
- Added logging to ``build`` and ``build.env`` (PR :pr:`333`)
- Switch to a TOML v1 compliant parser (PR :pr:`336`, Fixes :issue:`308`)

Breaking Changes
----------------

- Dropped support for Python 2 and 3.5.



0.5.1 (2021-06-22)
==================

- Fix invoking the backend on an inexistent output directory with multiple levels (PR :pr:`318`, Fixes :issue:`316`)
- When building wheels via sdists, use an isolated temporary directory (PR :pr:`321`, Fixes :issue:`320`)



0.5.0 (2021-06-19)
==================

- Add ``ProjectBuilder.metadata_path`` helper (PR :pr:`303`, Fixes :issue:`301`)
- Added a ``build.__main__.build_package_via_sdist`` method (PR :pr:`304`)
- Use appropriate installation scheme for Apple Python venvs (PR :pr:`314`, Fixes :issue:`310`)

Breaking Changes
----------------

- Binary distributions are now built via the sdist by default in the CLI (PR :pr:`304`, Fixes :issue:`257`)
  - ``python -m build`` will now build a sdist, extract it, and build a wheel from the source
- As a side-effect of PR :pr:`304`, ``build.__main__.build_package`` no longer does CLI error handling (print nice message and exit the program)
- Importing ``build.__main__`` no longer has any side-effects, it no longer overrides ``warnings.showwarning`` or runs ``colorama.init`` on import (PR :pr:`312`)



0.4.0 (2021-05-23)
==================

- Validate that the supplied source directory is valid (PR :pr:`260`, Fixes :issue:`259`)
- Set and test minimum versions of build's runtime dependencies (PR :pr:`267`, Fixes :issue:`263`)
- Use symlinks on creating venv's when available (PR :pr:`274`, Fixes :issue:`271`)
- Error sooner if pip upgrade is required and fails (PR :pr:`288`, Fixes :issue:`256`)
- Add a ``runner`` argument to ``ProjectBuilder`` (PR :pr:`290`, Fixes :issue:`289`)
- Hide irrelevant ``pep517`` error traceback and improve error messages (PR :pr:`296`)
- Try to use ``colorama`` to fix colors on Windows (PR :pr:`300`)

Breaking Changes
----------------

- As a side-effect of PR :pr:`260`, projects not containing either a ``pyproject.toml`` or ``setup.py`` will be reported as invalid. This affects projects specifying only a ``setup.cfg``, such projects are recommended to add a ``pyproject.toml``. The new behavior is on par with what pip currently does, so if you are affected by this, your project should not be pip installable.
- The ``--skip-dependencies`` option has been renamed to ``--skip-dependency-check`` (PR :pr:`297`)
- The ``skip_dependencies`` argument of ``build.__main__.build_package`` has been renamed to ``skip_dependency_check`` (PR :pr:`297`)
- ``build.ConfigSettings`` has been renamed to ``build.ConfigSettingsType`` (PR :pr:`298`)
- ``build.ProjectBuilder.build_dependencies`` to ``build.ProjectBuilder.build_system_requires`` (PR :pr:`284`, Fixes :issue:`182`)
- ``build.ProjectBuilder.get_dependencies`` to ``build.ProjectBuilder.get_requires_for_build`` (PR :pr:`284`, Fixes :issue:`182`)



0.3.1 (2021-03-09)
==================

- Support direct usage from pipx run in 0.16.1.0+ (PR :pr:`247`)
- Use UTF-8 encoding when reading pyproject.toml (PR :pr:`251`, Fixes :issue:`250`)



0.3.0 (2021-02-19)
==================

- Upgrade pip based on venv pip version, avoids error on Debian Python 3.6.5-3.8 or issues installing wheels on Big Sur (PR :pr:`229`, PR :pr:`230`, Fixes :issue:`228`)
- Build dependencies in isolation, instead of in the build environment (PR :pr:`232`, Fixes :issue:`231`)
- Fallback on venv if virtualenv is too old (PR :pr:`241`)
- Add metadata preparation hook (PR :pr:`217`, Fixes :issue:`130`)



0.2.1 (2021-02-09)
==================

- Fix error from unrecognised pip flag on Python 3.6.0 to 3.6.5 (PR :pr:`227`, Fixes :issue:`226`)



0.2.0 (2021-02-07)
==================

- Check dependencies recursively (PR :pr:`183`, Fixes :issue:`25`)
- Build wheel and sdist distributions in separate environments, as they may have different dependencies (PR :pr:`195`, Fixes :issue:`194`)
- Add support for pre-releases in ``check_dependency`` (PR :pr:`204`, Fixes :issue:`191`)
- Fixes console scripts not being available during build (PR :pr:`221`, Fixes :issue:`214`)
- Do not add the default backend requirements to ``requires`` when no backend is specified (PR :pr:`177`, Fixes :issue:`107`)
- Return the sdist name in ``ProjectBuild.build`` (PR :pr:`197`)
- Improve documentation (PR :pr:`178`, PR :pr:`203`)
- Add changelog (PR :pr:`219`, Fixes :issue:`169`)

Breaking changes
----------------

- Move ``config_settings`` argument to the hook calls (PR :pr:`218`, Fixes :issue:`216`)



0.1.0 (2020-10-29)
==================

- Moved the upstream to PyPA
- Fixed building with isolation in a virtual environment
- Added env.IsolatedEnv abstract class
- Added env.IsolatedEnvBuilder (replaces env.IsolatedEnvironment usages)
- Added python_executable argument to the ProjectBuilder constructor
- Added --version/-V option to the CLI
- Added support for Python 3.9
- Added py.typed marker
- Various miscellaneous fixes in the virtual environment creation
- Many general improvements in the documentation
- Documentation moved to the furo theme
- Updated the CoC to the PSF CoC, which PyPA has adopted

Breaking changes
----------------

- Renamed the entrypoint script to pyproject-build
- Removed default arguments from all paths in ProjectBuilder
- Removed ProjectBuilder.hook
- Renamed __main__.build to __main__.build_package
- Changed the default outdir value to {srcdir}/dest
- Removed env.IsolatedEnvironment



0.0.4 (2020-09-08)
==================

- Packages are now built in isolation by default
- Added --no-isolation/-n flag to build in the current environment
- Add --config-setting/-C option to pass options to the backend
- Add IsolatedEnvironment class
- Fix creating the output directory if it doesn't exit
- Fix building with in-tree backends
- Fix broken entrypoint script (python-build)
- Add warning about incomplete verification when verifying extras
- Automatically detect typos in the build system table
- Minor documentation improvements



0.0.3.1 (2020-06-10)
====================

- Fix bug preventing the CLI from being invoked
- Improved documentation



0.0.3 (2020-06-09)
==================

- Misc improvements
- Added documentation



0.0.2 (2020-05-29)
==================

- Add setuptools as a default fallback backend
- Fix extras handling in requirement strings



0.0.1 (2020-05-17)
==================

- Initial release
