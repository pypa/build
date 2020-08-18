# SPDX-License-Identifier: MIT

import argparse
import os
import sys
import traceback
import warnings

from typing import List, Optional, TextIO, Type

from . import BuildBackendException, BuildException, ConfigSettings, ProjectBuilder
from .env import IsolatedEnvironment


__all__ = ['build', 'main', 'main_parser']


def _showwarning(message, category, filename, lineno, file=None, line=None):  # pragma: no cover
    # type: (str, Type[Warning], str, int, Optional[TextIO], Optional[str]) -> None
    prefix = 'WARNING'
    if sys.stdout.isatty():
        prefix = '\33[93m' + prefix + '\33[0m'
    print('{} {}'.format(prefix, message))


warnings.showwarning = _showwarning


def _error(msg, code=1):  # type: (str, int) -> None  # pragma: no cover
    '''
    Prints an error message and exits. Will color the output when writting to a TTY.

    :param msg: Error message
    :param code: Error code
    '''
    prefix = 'ERROR'
    if sys.stdout.isatty():
        prefix = '\33[91m' + prefix + '\33[0m'
    print('{} {}'.format(prefix, msg))
    exit(code)


def _build_in_isolated_env(builder, outdir, distributions):  # type: (ProjectBuilder, str, List[str]) -> None
    with IsolatedEnvironment() as env:
        env.install(builder.build_dependencies)
        for distribution in distributions:
            builder.build(distribution, outdir)


def _build_in_current_env(builder, outdir, distributions, skip_dependencies=False):
    # type: (ProjectBuilder, str, List[str], bool) -> None
    for dist in distributions:
        if not skip_dependencies:
            missing = builder.check_dependencies(dist)
            if missing:
                _error('Missing dependencies:' + ''.join(['\n\t' + dep for dep in missing]))

        builder.build(dist, outdir)


def build(srcdir, outdir, distributions, config_settings=None, isolation=True, skip_dependencies=False):
    # type: (str, str, List[str], Optional[ConfigSettings], bool, bool) -> None
    '''
    Runs the build process

    :param srcdir: Source directory
    :param outdir: Output directory
    :param distributions: Distributions to build (sdist and/or wheel)
    :param config_settings: Configuration settings to be passed to the backend
    :param isolation: Isolate the build in a separate environment
    :param skip_dependencies: Do not perform the dependency check
    '''
    if not config_settings:
        config_settings = {}

    try:
        builder = ProjectBuilder(srcdir, config_settings)

        if isolation:
            _build_in_isolated_env(builder, outdir, distributions)
        else:
            _build_in_current_env(builder, outdir, distributions, skip_dependencies)
    except BuildException as e:
        _error(str(e))
    except BuildBackendException as e:
        if sys.version_info >= (3, 5):
            print(traceback.format_exc(-1))
        else:
            print(traceback.format_exc())
        _error(str(e))


def main_parser():  # type: () -> argparse.ArgumentParser
    '''
    Constructs the main parser
    '''
    cwd = os.getcwd()
    out = os.path.join(cwd, 'dist')
    parser = argparse.ArgumentParser()
    parser.add_argument('srcdir',
                        type=str, nargs='?', metavar='.', default=cwd,
                        help='source directory (defaults to current directory)')
    parser.add_argument('--sdist', '-s',
                        action='store_true',
                        help='build a source package')
    parser.add_argument('--wheel', '-w',
                        action='store_true',
                        help='build a wheel')
    parser.add_argument('--outdir', '-o', metavar='dist',
                        type=str, default=out,
                        help='output directory')
    parser.add_argument('--skip-dependencies', '-x',
                        action='store_true',
                        help='does not check for the dependencies')
    parser.add_argument('--no-isolation', '-n',
                        action='store_true',
                        help='do not isolate the build in a virtual environment')
    parser.add_argument('--config-setting', '-C',
                        action='append',
                        help='pass option to the backend')
    return parser


def main(cli_args, prog=None):  # type: (List[str], Optional[str]) -> None
    '''
    Parses the CLI arguments and invokes the build process.

    :param cli_args: CLI arguments
    '''
    parser = main_parser()
    if prog:
        parser.prog = prog
    args = parser.parse_args(cli_args)

    distributions = []
    config_settings = {}

    if args.config_setting:
        for arg in args.config_setting:
            if sys.version_info >= (3,):
                data = arg.split('=', maxsplit=1)
            else:
                split_data = arg.split('=')
                data = [
                    split_data[0],
                    '='.join(split_data[1:]),
                ]
            setting = data[0]
            value = data[1] if len(data) >= 2 else ''

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

    build(args.srcdir, args.outdir, distributions, config_settings, not args.no_isolation, args.skip_dependencies)


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:], 'python -m build')
