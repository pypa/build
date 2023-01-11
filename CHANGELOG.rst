+++++++++
Changelog
+++++++++


0.10.0 (2023-01-11)
===================

- Replace ``pep517`` dependency with ``pyproject_hooks``,
  into which ``pep517`` has been renamed
  (`PR #539`_, Fixes `#529`_)
- Change build backend from ``setuptools`` to ``flit``
  (`PR #470`_, Fixes `#394`_)
- Dropped support for Python 3.6 (`PR #532`_)

.. _PR #470: https://github.com/pypa/build/pull/470
.. _PR #532: https://github.com/pypa/build/pull/532
.. _#394: https://github.com/pypa/build/issues/394
.. _PR #539: https://github.com/pypa/build/pull/539
.. _#529: https://github.com/pypa/build/issues/529


0.9.0 (2022-10-27)
==================

- Hide a Python 3.11.0 unavoidable warning with venv (`PR #527`_)
- Fix infinite recursion error in ``check_dependency`` with circular
  dependencies (`PR #512`_, Fixes `#511`_)
- Only import colorama on Windows (`PR #494`_, Fixes `#493`_)
- Flush output more often to reduce interleaved output (`PR #494`_)
- Small API cleanup, like better ``__all__`` and srcdir being read only. (`PR #477`_)
- Only use ``importlib_metadata`` when needed (`PR #401`_)
- Clarify in printout when build dependencies are being installed (`PR #514`_)

.. _PR #401: https://github.com/pypa/build/pull/401
.. _PR #477: https://github.com/pypa/build/pull/477
.. _PR #494: https://github.com/pypa/build/pull/494
.. _PR #512: https://github.com/pypa/build/pull/512
.. _PR #514: https://github.com/pypa/build/pull/514
.. _PR #527: https://github.com/pypa/build/pull/527
.. _#493: https://github.com/pypa/build/issues/493
.. _#511: https://github.com/pypa/build/issues/511


0.8.0 (2022-05-22)
==================

- Accept ``os.PathLike[str]`` in addition to ``str`` for paths in public
  API (`PR #392`_, Fixes `#372`_)
- Add schema validation for ``build-system`` table to check conformity
  with PEP 517 and PEP 518 (`PR #365`_, Fixes `#364`_)
- Better support for Python 3.11 (sysconfig schemes `PR #434`_,  `PR #463`_, tomllib `PR #443`_, warnings `PR #420`_)
- Improved error printouts (`PR #442`_)
- Avoid importing packaging unless needed (`PR #395`_, Fixes `#393`_)


Breaking Changes
----------------

- Failure to create a virtual environment in the ``build.env`` module now raises
  ``build.FailedProcessError`` (`PR #442`_)

.. _PR #365: https://github.com/pypa/build/pull/365
.. _PR #392: https://github.com/pypa/build/pull/392
.. _PR #395: https://github.com/pypa/build/pull/395
.. _PR #420: https://github.com/pypa/build/pull/420
.. _PR #434: https://github.com/pypa/build/pull/434
.. _PR #442: https://github.com/pypa/build/pull/442
.. _PR #443: https://github.com/pypa/build/pull/443
.. _PR #463: https://github.com/pypa/build/pull/463
.. _#364: https://github.com/pypa/build/issues/364
.. _#372: https://github.com/pypa/build/issues/372
.. _#393: https://github.com/pypa/build/pull/393


0.7.0 (2021-09-16)
==================

- Add ``build.util`` module with an high-level utility API (`PR #340`_)

.. _PR #340: https://github.com/pypa/build/pull/340


0.6.0.post1 (2021-08-05)
========================

- Fix compatibility with Python 3.6 and 3.7 (`PR #339`_, Fixes `#338`_)

.. _PR #339: https://github.com/pypa/build/pull/339
.. _#338: https://github.com/pypa/build/issues/338



0.6.0 (2021-08-02)
==================

- Improved output (`PR #333`_, Fixes `#142`_)
- The CLI now honors `NO_COLOR`_ (`PR #333`_)
- The CLI can now be forced to colorize the output by setting the ``FORCE_COLOR`` environment variable (`PR #335`_)
- Added logging to ``build`` and ``build.env`` (`PR #333`_)
- Switch to a TOML v1 compliant parser (`PR #336`_, Fixes `#308`_)


Breaking Changes
----------------

- Dropped support for Python 2 and 3.5.

.. _PR #333: https://github.com/pypa/build/pull/333
.. _PR #335: https://github.com/pypa/build/pull/335
.. _PR #336: https://github.com/pypa/build/pull/336
.. _#142: https://github.com/pypa/build/issues/142
.. _#308: https://github.com/pypa/build/issues/308
.. _NO_COLOR: https://no-color.org



0.5.1 (2021-06-22)
==================

- Fix invoking the backend on an inexistent output directory with multiple levels (`PR #318`_, Fixes `#316`_)
- When building wheels via sdists, use an isolated temporary directory (`PR #321`_, Fixes `#320`_)

.. _PR #318: https://github.com/pypa/build/pull/318
.. _PR #321: https://github.com/pypa/build/pull/321
.. _#316: https://github.com/pypa/build/issues/316
.. _#320: https://github.com/pypa/build/issues/320



0.5.0 (2021-06-19)
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



0.4.0 (2021-05-23)
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
- The ``--skip-dependencies`` option has been renamed to ``--skip-dependency-check`` (`PR #297`_)
- The ``skip_dependencies`` argument of ``build.__main__.build_package`` has been renamed to ``skip_dependency_check`` (`PR #297`_)
- ``build.ConfigSettings`` has been renamed to ``build.ConfigSettingsType`` (`PR #298`_)
- ``build.ProjectBuilder.build_dependencies`` to ``build.ProjectBuilder.build_system_requires`` (`PR #284`_, Fixes `#182`_)
- ``build.ProjectBuilder.get_dependencies`` to ``build.ProjectBuilder.get_requires_for_build`` (`PR #284`_, Fixes `#182`_)

.. _PR #284: https://github.com/pypa/build/pull/284
.. _PR #297: https://github.com/pypa/build/pull/297
.. _PR #298: https://github.com/pypa/build/pull/298
.. _#182: https://github.com/pypa/build/issues/182



0.3.1 (2021-03-09)
==================

- Support direct usage from pipx run in 0.16.1.0+ (`PR #247`_)
- Use UTF-8 encoding when reading pyproject.toml (`PR #251`_, Fixes `#250`_)

.. _PR #247: https://github.com/pypa/build/pull/247
.. _PR #251: https://github.com/pypa/build/pull/251
.. _#250: https://github.com/pypa/build/issues/250



0.3.0 (2021-02-19)
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



0.2.1 (2021-02-09)
==================

- Fix error from unrecognised pip flag on Python 3.6.0 to 3.6.5 (`PR #227`_, Fixes `#226`_)

.. _PR #227: https://github.com/pypa/build/pull/227
.. _#226: https://github.com/pypa/build/issues/226



0.2.0 (2021-02-07)
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
