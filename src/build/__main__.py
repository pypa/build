# SPDX-License-Identifier: MIT

import argparse
import os
import sys
import traceback
import warnings

from typing import Iterable, List, Optional, Sequence, TextIO, Type, Union

import build

from build import BuildBackendException, BuildException, ConfigSettings, ProjectBuilder
from build.env import IsolatedEnvBuilder


__all__ = ['build', 'main', 'main_parser']


def _showwarning(message, category, filename, lineno, file=None, line=None):  # pragma: no cover
    # type: (Union[Warning, str], Type[Warning], str, int, Optional[TextIO], Optional[str]) -> None
    prefix = 'WARNING'
    if sys.stdout.isatty():
        prefix = '\33[93m' + prefix + '\33[0m'
    print('{} {}'.format(prefix, str(message)))


warnings.showwarning = _showwarning


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


def _build_in_isolated_env(builder, outdir, distributions, config_settings):
    # type: (ProjectBuilder, str, List[str], ConfigSettings) -> None
    for distribution in distributions:
        with IsolatedEnvBuilder() as env:
            builder.python_executable = env.executable
            builder.scripts_dir = env.scripts_dir
            # first install the build dependencies
            env.install(builder.build_dependencies)
            # then get the extra required dependencies from the backend (which was installed in the call above :P)
            env.install(builder.get_dependencies(distribution))
            builder.build(distribution, outdir, config_settings)


def _build_in_current_env(builder, outdir, distributions, config_settings, skip_dependencies=False):
    # type: (ProjectBuilder, str, List[str], ConfigSettings, bool) -> None
    for dist in distributions:
        if not skip_dependencies:
            missing = builder.check_dependencies(dist)
            if missing:
                _error(
                    'Missing dependencies:'
                    + ''.join('\n\t' + dep for deps in missing for dep in (deps[0], _format_dep_chain(deps[1:])) if dep)
                )

        builder.build(dist, outdir, config_settings)


def build_package(srcdir, outdir, distributions, config_settings=None, isolation=True, skip_dependencies=False):
    # type: (str, str, List[str], Optional[ConfigSettings], bool, bool) -> None
    """
    Run the build process.

    :param srcdir: Source directory
    :param outdir: Output directory
    :param distributions: Distributions to build (sdist and/or wheel)
    :param config_settings: Configuration settings to be passed to the backend
    :param isolation: Isolate the build in a separate environment
    :param skip_dependencies: Do not perform the dependency check
    """
    if not config_settings:
        config_settings = {}

    try:
        builder = ProjectBuilder(srcdir)
        if isolation:
            _build_in_isolated_env(builder, outdir, distributions, config_settings)
        else:
            _build_in_current_env(builder, outdir, distributions, config_settings, skip_dependencies)
    except BuildException as e:
        _error(str(e))
    except BuildBackendException as e:
        if sys.version_info >= (3, 5):
            print(traceback.format_exc(-1))
        else:
            print(traceback.format_exc())
        _error(str(e))


def main_parser():  # type: () -> argparse.ArgumentParser
    """
    Construct the main parser.
    """
    # mypy does not recognize module.__path__
    # https://github.com/python/mypy/issues/1422
    paths = build.__path__  # type: Iterable[Optional[str]]  # type: ignore
    parser = argparse.ArgumentParser()
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
        help='build a source distribution',
    )
    parser.add_argument(
        '--wheel',
        '-w',
        action='store_true',
        help='build a wheel',
    )
    parser.add_argument(
        '--outdir',
        '-o',
        type=str,
        help='output directory (defaults to {{srcdir}}{sep}dist)'.format(sep=os.sep),
    )
    parser.add_argument(
        '--skip-dependencies',
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


def main(cli_args, prog=None):  # type: (List[str], Optional[str]) -> None
    """
    Parse the CLI arguments and invoke the build process.

    :param cli_args: CLI arguments
    :param prog: Program name to show in help text
    """
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

    # default targets
    if not distributions:
        distributions = ['sdist', 'wheel']

    # outdir is relative to srcdir only if omitted.
    outdir = os.path.join(args.srcdir, 'dist') if args.outdir is None else args.outdir

    build_package(args.srcdir, outdir, distributions, config_settings, not args.no_isolation, args.skip_dependencies)


def entrypoint():  # type: () -> None
    main(sys.argv[1:])


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:], 'python -m build')
