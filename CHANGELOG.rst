+++++++++
Changelog
+++++++++


0.5.0 (19-06-2021)
==================

- Add ``ProjectBuilder.metadata_path`` helper (`PR #303`_, Fixes `#301`_)
- Added a ``build.__main__.build_package_via_sdist`` method (`PR #304`_)
- Use appropriate installation scheme for Apple Python venvs (`PR #314`_, Fixes `#310`_)

Breaking Changes
----------------

- Binary distributions are now built via the sdist by default in the CLI (`PR #304`_, Fixes `#257`_)
  - ``python -m build`` will now build a sdist, extract it, and build a wheel from the source
- As a side-effect of `PR #304`_, ``build.__main__.build_package`` no longer does CLI error handling (print nice message and exit the program)
- Importing ``build.__main__`` no longer has any side-effects, it no longer overrides ``warnings.showwarning`` or runs ``colorama.init`` on import (`PR #312`_)

.. _PR #303: https://github.com/pypa/build/pull/303
.. _PR #304: https://github.com/pypa/build/pull/304
.. _PR #312: https://github.com/pypa/build/pull/312
.. _PR #314: https://github.com/pypa/build/pull/314
.. _#257: https://github.com/pypa/build/issues/257
.. _#301: https://github.com/pypa/build/issues/301
.. _#310: https://github.com/pypa/build/issues/310



0.4.0 (23-05-2021)
==================

- Validate that the supplied source directory is valid (`PR #260`_, Fixes `#259`_)
- Set and test minimum versions of build's runtime dependencies (`PR #267`_, Fixes `#263`_)
- Use symlinks on creating venv's when available (`PR #274`_, Fixes `#271`_)
- Error sooner if pip upgrade is required and fails (`PR #288`_, Fixes `#256`_)
- Add a ``runner`` argument to ``ProjectBuilder`` (`PR #290`_, Fixes `#289`_)
- Hide irrelevant ``pep517`` error traceback and improve error messages (`PR #296`_)
- Try to use ``colorama`` to fix colors on Windows (`PR #300`_)

.. _PR #260: https://github.com/pypa/build/pull/260
.. _PR #267: https://github.com/pypa/build/pull/267
.. _PR #274: https://github.com/pypa/build/pull/274
.. _PR #288: https://github.com/pypa/build/pull/288
.. _PR #290: https://github.com/pypa/build/pull/290
.. _PR #296: https://github.com/pypa/build/pull/296
.. _PR #300: https://github.com/pypa/build/pull/300
.. _#256: https://github.com/pypa/build/issues/256
.. _#259: https://github.com/pypa/build/issues/259
.. _#263: https://github.com/pypa/build/issues/263
.. _#271: https://github.com/pypa/build/issues/271
.. _#289: https://github.com/pypa/build/issues/289

Breaking Changes
----------------

- As a side-effect of `PR #260`_, projects not containing either a ``pyproject.toml`` or ``setup.py`` will be reported as invalid. This affects projects specifying only a ``setup.cfg``, such projects are recommended to add a ``pyproject.toml``. The new behavior is on par with what pip currently does, so if you are affected by this, your project should not be pip installable.
- The ``--skip-depencencies`` option has been renamed to ``--skip-dependency-check`` (`PR #297`_)
- The ``skip_dependencies`` argument of ``build.__main__.build_package`` has been renamed to ``skip_dependency_check`` (`PR #297`_)
- ``build.ConfigSettings`` has been renamed to ``build.ConfigSettingsType`` (`PR #298`_)
- ``build.ProjectBuilder.build_dependencies`` to ``build.ProjectBuilder.build_system_requires`` (`PR #284`_, Fixes `#182`_)
- ``build.ProjectBuilder.get_dependencies`` to ``build.ProjectBuilder.get_requires_for_build`` (`PR #284`_, Fixes `#182`_)

.. _PR #284: https://github.com/pypa/build/pull/284
.. _PR #297: https://github.com/pypa/build/pull/297
.. _PR #298: https://github.com/pypa/build/pull/298
.. _#182: https://github.com/pypa/build/issues/182



0.3.1 (09-03-2021)
==================

- Support direct usage from pipx run in 0.16.1.0+ (`PR #247`_)
- Use UTF-8 encoding when reading pyproject.toml (`PR #251`_, Fixes `#250`_)

.. _PR #247: https://github.com/pypa/build/pull/247
.. _PR #251: https://github.com/pypa/build/pull/251
.. _#250: https://github.com/pypa/build/issues/250



0.3.0 (19-02-2021)
==================

- Upgrade pip based on venv pip version, avoids error on Debian Python 3.6.5-3.8 or issues installing wheels on Big Sur (`PR #229`_, `PR #230`_, Fixes `#228`_)
- Build dependencies in isolation, instead of in the build environment (`PR #232`_, Fixes `#231`_)
- Fallback on venv if virtualenv is too old (`PR #241`_)
- Add metadata preparation hook (`PR #217`_, Fixes `#130`_)

.. _PR #217: https://github.com/pypa/build/pull/217
.. _PR #229: https://github.com/pypa/build/pull/229
.. _PR #230: https://github.com/pypa/build/pull/230
.. _PR #232: https://github.com/pypa/build/pull/232
.. _PR #241: https://github.com/pypa/build/pull/241
.. _#130: https://github.com/pypa/build/issues/130
.. _#228: https://github.com/pypa/build/issues/228
.. _#231: https://github.com/pypa/build/issues/231



0.2.1 (09-02-2021)
==================

- Fix error from unrecognised pip flag on Python 3.6.0 to 3.6.5 (`PR #227`_, Fixes `#226`_)

.. _PR #227: https://github.com/pypa/build/pull/227
.. _#226: https://github.com/pypa/build/issues/226



0.2.0 (07-02-2021)
==================

- Check dependencies recursively (`PR #183`_, Fixes `#25`_)
- Build wheel and sdist distributions in separate environments, as they may have different dependencies (`PR #195`_, Fixes `#194`_)
- Add support for pre-releases in ``check_dependency`` (`PR #204`_, Fixes `#191`_)
- Fixes console scripts not being available during build (`PR #221`_, Fixes `#214`_)
- Do not add the default backend requirements to ``requires`` when no backend is specified (`PR #177`_, Fixes `#107`_)
- Return the sdist name in ``ProjectBuild.build`` (`PR #197`_)
- Improve documentation (`PR #178`_, `PR #203`_)
- Add changelog (`PR #219`_, Fixes `#169`_)

Breaking changes
----------------

- Move ``config_settings`` argument to the hook calls (`PR #218`_, Fixes `#216`_)

.. _PR #177: https://github.com/pypa/build/pull/177
.. _PR #178: https://github.com/pypa/build/pull/178
.. _PR #183: https://github.com/pypa/build/pull/183
.. _PR #195: https://github.com/pypa/build/pull/195
.. _PR #197: https://github.com/pypa/build/pull/197
.. _PR #203: https://github.com/pypa/build/pull/203
.. _PR #204: https://github.com/pypa/build/pull/204
.. _PR #218: https://github.com/pypa/build/pull/218
.. _PR #219: https://github.com/pypa/build/pull/219
.. _PR #221: https://github.com/pypa/build/pull/221
.. _#25: https://github.com/pypa/build/issues/25
.. _#107: https://github.com/pypa/build/issues/107
.. _#109: https://github.com/pypa/build/issues/109
.. _#169: https://github.com/pypa/build/issues/169
.. _#191: https://github.com/pypa/build/issues/191
.. _#194: https://github.com/pypa/build/issues/194
.. _#214: https://github.com/pypa/build/issues/214
.. _#216: https://github.com/pypa/build/issues/216



0.1.0 (29-10-2020)
==================

- Moved the upstream to PyPA
- Fixed building with isolation in a virtual environment
- Added env.IsolatedEnv abstract class
- Added env.IsolatedEnvBuilder (replaces env.IsolatedEnvironment usages)
- Added python_executable argument to the ProjectBuilder constructor
- Added --version/-V option to the CLI
- Added support for Python 3.9
- Added py.typed marker
- Various miscelaneous fixes in the virtual environment creation
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



0.0.4 (08-09-2020)
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



0.0.3.1 (10-06-2020)
====================

- Fix bug preventing the CLI from being invoked
- Improved documentation



0.0.3 (09-06-2020)
==================

- Misc improvements
- Added documentation



0.0.2 (29-05-2020)
==================

- Add setuptools as a default fallback backend
- Fix extras handling in requirement strings



0.0.1 (17-05-2020)
==================

- Initial release
