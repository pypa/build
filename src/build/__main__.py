# SPDX-License-Identifier: MIT

from __future__ import print_function

import argparse
import contextlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import traceback
import warnings

from typing import Iterable, Iterator, List, Optional, Sequence, TextIO, Type, Union

import build

from build import BuildBackendException, BuildException, ConfigSettingsType, ProjectBuilder
from build.env import IsolatedEnvBuilder


__all__ = ['build', 'main', 'main_parser']


if sys.version_info[0] == 2:

    def _indent(text, prefix):  # type: (str, str) -> str
        return ''.join(prefix + line for line in text.splitlines(True))


else:
    from textwrap import indent as _indent


def _showwarning(message, category, filename, lineno, file=None, line=None):  # pragma: no cover
    # type: (Union[Warning, str], Type[Warning], str, int, Optional[TextIO], Optional[str]) -> None
    prefix = 'WARNING'
    if sys.stdout.isatty():
        prefix = '\33[93m' + prefix + '\33[0m'
    print('{} {}'.format(prefix, str(message)))


def _setup_cli():  # type: () -> None
    warnings.showwarning = _showwarning

    try:
        import colorama
    except ImportError:
        pass
    else:
        colorama.init()  # fix colors on windows


def _error(msg, code=1):  # type: (str, int) -> None  # pragma: no cover
    """
    Print an error message and exit. Will color the output when writing to a TTY.

    :param msg: Error message
    :param code: Error code
    """
    prefix = 'ERROR'
    if sys.stdout.isatty():
        prefix = '\33[91m' + prefix + '\33[0m'
    print('{} {}'.format(prefix, msg))
    exit(code)


def _format_dep_chain(dep_chain):  # type: (Sequence[str]) -> str
    return ' -> '.join(dep.partition(';')[0].strip() for dep in dep_chain)


def _build_in_isolated_env(builder, outdir, distribution, config_settings):
    # type: (ProjectBuilder, str, str, Optional[ConfigSettingsType]) -> str
    with IsolatedEnvBuilder() as env:
        builder.python_executable = env.executable
        builder.scripts_dir = env.scripts_dir
        # first install the build dependencies
        env.install(builder.build_system_requires)
        # then get the extra required dependencies from the backend (which was installed in the call above :P)
        env.install(builder.get_requires_for_build(distribution))
        return builder.build(distribution, outdir, config_settings or {})


def _build_in_current_env(builder, outdir, distribution, config_settings, skip_dependency_check=False):
    # type: (ProjectBuilder, str, str, Optional[ConfigSettingsType], bool) -> str
    if not skip_dependency_check:
        missing = builder.check_dependencies(distribution)
        if missing:
            dependencies = ''.join('\n\t' + dep for deps in missing for dep in (deps[0], _format_dep_chain(deps[1:])) if dep)
            _error('Missing dependencies:{}'.format(dependencies))

    return builder.build(distribution, outdir, config_settings or {})


def _build(isolation, builder, outdir, distribution, config_settings, skip_dependency_check):
    # type: (bool, ProjectBuilder, str, str, Optional[ConfigSettingsType], bool) -> str
    if isolation:
        return _build_in_isolated_env(builder, outdir, distribution, config_settings)
    else:
        return _build_in_current_env(builder, outdir, distribution, config_settings, skip_dependency_check)


@contextlib.contextmanager
def _handle_build_error():  # type: () -> Iterator[None]
    try:
        yield
    except BuildException as e:
        _error(str(e))
    except BuildBackendException as e:
        if isinstance(e.exception, subprocess.CalledProcessError):
            print()
        else:
            if e.exc_info:
                traceback.print_exception(
                    e.exc_info[0],
                    e.exc_info[1],
                    e.exc_info[2],
                    limit=-1,
                )
            else:
                if sys.version_info >= (3, 5):
                    print(traceback.format_exc(-1))
                else:
                    print(traceback.format_tb())
        _error(str(e))


def build_package(srcdir, outdir, distributions, config_settings=None, isolation=True, skip_dependency_check=False):
    # type: (str, str, List[str], Optional[ConfigSettingsType], bool, bool) -> None
    """
    Run the build process.

    :param srcdir: Source directory
    :param outdir: Output directory
    :param distribution: Distribution to build (sdist or wheel)
    :param config_settings: Configuration settings to be passed to the backend
    :param isolation: Isolate the build in a separate environment
    :param skip_dependency_check: Do not perform the dependency check
    """
    builder = ProjectBuilder(srcdir)
    for distribution in distributions:
        _build(isolation, builder, outdir, distribution, config_settings, skip_dependency_check)


def build_package_via_sdist(srcdir, outdir, distributions, config_settings=None, isolation=True, skip_dependency_check=False):
    # type: (str, str, List[str], Optional[ConfigSettingsType], bool, bool) -> None
    """
    Build a sdist and then the specified distributions from it.

    :param srcdir: Source directory
    :param outdir: Output directory
    :param distribution: Distribution to build (only wheel)
    :param config_settings: Configuration settings to be passed to the backend
    :param isolation: Isolate the build in a separate environment
    :param skip_dependency_check: Do not perform the dependency check
    """
    if 'sdist' in distributions:
        raise ValueError('Only binary distributions are allowed but sdist was specified')

    builder = ProjectBuilder(srcdir)
    sdist = _build(isolation, builder, outdir, 'sdist', config_settings, skip_dependency_check)

    sdist_name = os.path.basename(sdist)
    sdist_out = tempfile.mkdtemp(prefix='build-via-sdist-')
    # extract sdist
    with tarfile.open(sdist) as t:
        t.extractall(sdist_out)
        try:
            builder = ProjectBuilder(os.path.join(sdist_out, sdist_name[: -len('.tar.gz')]))
            for distribution in distributions:
                _build(isolation, builder, outdir, distribution, config_settings, skip_dependency_check)
        finally:
            shutil.rmtree(sdist_out, ignore_errors=True)


def main_parser():  # type: () -> argparse.ArgumentParser
    """
    Construct the main parser.
    """
    # mypy does not recognize module.__path__
    # https://github.com/python/mypy/issues/1422
    paths = build.__path__  # type: Iterable[Optional[str]]  # type: ignore
    parser = argparse.ArgumentParser(
        description=_indent(  # textwrap.indent
            textwrap.dedent(
                '''
                A simple, correct PEP 517 package builder.

                By default, a source distribution (sdist) is built from {srcdir}
                and a binary distribution (wheel) is built from the sdist.
                This is recommended as it will ensure the sdist can be used
                to build wheels.

                Pass -s/--sdist and/or -w/--wheel to build a specific distribution.
                If you do this, the default behavior will be disabled, and all
                artifacts will be built from {srcdir} (even if you combine
                -w/--wheel with -s/--sdist, the wheel will be built from {srcdir}).
                '''
            ).strip(),
            '    ',
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        'srcdir',
        type=str,
        nargs='?',
        default=os.getcwd(),
        help='source directory (defaults to current directory)',
    )
    parser.add_argument(
        '--version',
        '-V',
        action='version',
        version='build {} ({})'.format(build.__version__, ', '.join(path for path in paths if path)),
    )
    parser.add_argument(
        '--sdist',
        '-s',
        action='store_true',
        help='build a source distribution (disables the default behavior)',
    )
    parser.add_argument(
        '--wheel',
        '-w',
        action='store_true',
        help='build a wheel (disables the default behavior)',
    )
    parser.add_argument(
        '--outdir',
        '-o',
        type=str,
        help='output directory (defaults to {{srcdir}}{sep}dist)'.format(sep=os.sep),
    )
    parser.add_argument(
        '--skip-dependency-check',
        '-x',
        action='store_true',
        help='do not check that build dependencies are installed',
    )
    parser.add_argument(
        '--no-isolation',
        '-n',
        action='store_true',
        help='do not isolate the build in a virtual environment',
    )
    parser.add_argument(
        '--config-setting',
        '-C',
        action='append',
        help='pass options to the backend.  options which begin with a hyphen must be in the form of '
        '"--config-setting=--opt(=value)" or "-C--opt(=value)"',
    )
    return parser


def main(cli_args, prog=None):  # type: (List[str], Optional[str]) -> None  # noqa: C901
    """
    Parse the CLI arguments and invoke the build process.

    :param cli_args: CLI arguments
    :param prog: Program name to show in help text
    """
    _setup_cli()
    parser = main_parser()
    if prog:
        parser.prog = prog
    args = parser.parse_args(cli_args)

    distributions = []
    config_settings = {}

    if args.config_setting:
        for arg in args.config_setting:
            setting, _, value = arg.partition('=')
            if setting not in config_settings:
                config_settings[setting] = value
            else:
                if not isinstance(config_settings[setting], list):
                    config_settings[setting] = [config_settings[setting]]

                config_settings[setting].append(value)

    if args.sdist:
        distributions.append('sdist')
    if args.wheel:
        distributions.append('wheel')

    # outdir is relative to srcdir only if omitted.
    outdir = os.path.join(args.srcdir, 'dist') if args.outdir is None else args.outdir

    if distributions:
        build_call = build_package
    else:
        build_call = build_package_via_sdist
        distributions = ['wheel']
    try:
        with _handle_build_error():
            build_call(args.srcdir, outdir, distributions, config_settings, not args.no_isolation, args.skip_dependency_check)
    except Exception as e:  # pragma: no cover
        print(traceback.format_exc())
        _error(str(e))


def entrypoint():  # type: () -> None
    main(sys.argv[1:])


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:], 'python -m build')
