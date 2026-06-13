# AGENTS.md

`build` is a PEP 517/518 build frontend: it builds sdists and wheels by invoking a project's build backend (setuptools, flit, hatchling, …) in an isolated environment.

## Commands

- **Lint:** `prek -a --quiet` (runs pre-commit hooks via `prek`)
- **Type check:** `uv run --group mypy mypy`
- **Test (unit only):** `uv run --group test pytest` (integration tests are skipped by default)
- **Test (with integration):** `uv run --group test pytest --run-integration`
- **Test (only integration):** `uv run --group test pytest --only-integration`
- **Single test file:** `uv run --group test pytest tests/test_util.py`
- **Full CI via tox:** `tox -e fix,type,3.10` (requires `tox-uv`)

## Architecture

- **Entrypoint:** `src/build/__main__.py` (CLI via `pyproject-build` script)
- **Core builder:** `src/build/_builder.py` (`ProjectBuilder`)
- **Environment management:** `src/build/env.py` (isolated venv creation with pip/uv/virtualenv backends)
- **Public helpers:** `src/build/util.py` (e.g. `project_wheel_metadata`) — the public API surface; `src/build/_util.py` is internal
- **Logging/verbosity:** `src/build/_ctx.py` (a `contextvars`-based logger + verbosity level shared across the build)
- **Exceptions:** `src/build/_exceptions.py` (`BuildException`, `BuildBackendException`, `FailedProcessError`)
- **Compatibility shims:** `src/build/_compat/` (tomllib, importlib, tarfile)
- **Types (generated):** `src/build/_types.py` — do not hand-edit; contains `Protocol` definitions
- **Build system:** flit-core (version read from `src/build/__init__.py` `__version__`)

## Lazy imports

The main modules use `__lazy_modules__` + deferred imports to keep startup fast. If you add a new public module, add it to `__lazy_modules__` in the appropriate file. Checked in pre-commit.

## Testing

- Integration tests live in `test_integration.py` and require `--run-integration` flag
- Test packages under `tests/packages/` are fixture projects (setuptools, flit, bad-syntax, etc.) used by parametrized tests
- `conftest.py` auto-generates per-package fixtures named `package_{normalized_name}`
- The `has_virtualenv` fixture is autouse and defaults to `False`; parametrize with `[True, False]` when testing virtualenv behavior
- Coverage uses `sysmon` core and excludes `test_integration.py` and `conftest.py`
- PyPy 3 Windows venv bugs are handled via `pypy3323bug` marker + `PYPY3323BUG` env var

## Style

- Ruff with `select = ["ALL"]` and many ignores (see `pyproject.toml`)
- `typing.TYPE_CHECKING` is banned — use `TYPE_CHECKING=False` instead
- Quote style: single quotes (formatter-enforced)
- Line length: 127

## Version bumping

Uses `bump-my-version`. Config in `pyproject.toml` under `[tool.bumpversion]`. Updates both `pyproject.toml` and `src/build/__init__.py`.

## Changelog

Towncrier fragments go in `docs/changelog/` as `N.type.rst` (types: feature, bugfix, doc, removal, misc). A pre-commit hook enforces the naming convention.
