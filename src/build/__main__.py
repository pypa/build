# SPDX-License-Identifier: MIT

import argparse
import os
import sys
import traceback
import warnings
from collections import defaultdict
from typing import List, Optional, TextIO, Type

from build import BuildBackendException, BuildException, ConfigSettings, ProjectBuilder
from build.env import IsolatedEnvironment, Isolation

__all__ = ['build', 'main', 'main_parser']


def _showwarning(message, category, filename, lineno, file=None, line=None):  # pragma: no cover
    # type: (str, Type[Warning], str, int, Optional[TextIO], Optional[str]) -> None
    prefix = 'WARNING'
    if sys.stdout.isatty():
        prefix = '\33[93m' + prefix + '\33[0m'
    print('{} {}'.format(prefix, message))


warnings.showwarning = _showwarning


def _error(msg, code=1):  # type: (str, int) -> None  # pragma: no cover
    """
    Prints an error message and exits. Will color the output when writting to a TTY.

    :param msg: Error message
    :param code: Error code
    """
    prefix = 'ERROR'
    if sys.stdout.isatty():
        prefix = '\33[91m' + prefix + '\33[0m'
    print('{} {}'.format(prefix, msg))
    exit(code)


def _build_in_isolated_env(builder, outdir, distributions, isolation):
    # type: (ProjectBuilder, str, List[str], Isolation) -> None
    with IsolatedEnvironment.for_current(isolation) as env:
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


def build(srcdir, outdir, distributions, isolation, config_settings=None, skip_dependencies=False):
    # type: (str, str, List[str], Isolation, Optional[ConfigSettings], bool) -> None
    """
    Runs the build process

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
        builder = ProjectBuilder(srcdir, config_settings)

        if isolation.enabled:
            _build_in_isolated_env(builder, outdir, distributions, isolation)
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
    """
    Constructs the main parser
    """
    cwd = os.getcwd()
    out = os.path.join(cwd, 'dist')

    class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
        def __init__(self, prog):
            super(HelpFormatter, self).__init__(prog, max_help_position=32, width=240)

    parser = argparse.ArgumentParser(formatter_class=HelpFormatter)
    parser.add_argument(
        'srcdir',
        type=str,
        nargs='?',
        metavar='sourcedir',
        default=cwd,
        help='source directory (defaults to current directory)',
    )
    parser.add_argument(
        '--sdist',
        '-s',
        action='store_true',
        help='build a source package',
    )
    parser.add_argument(
        '--wheel',
        '-w',
        action='store_true',
        help='build a wheel',
    )
    parser.add_argument('--outdir', '-o', metavar='dist', type=str, default=out, help='output directory')
    parser.add_argument(
        '--skip-dependencies',
        '-x',
        action='store_true',
        help='does not check for the dependencies',
    )
    parser.add_argument(
        '--config-setting',
        '-C',
        action='append',
        metavar='k=v',
        type=config_setting,
        help='pass option to the backend',
        default=[],
    )

    group = parser.add_argument_group('isolation options')
    default_isolation = Isolation()
    group = group.add_mutually_exclusive_group()
    group.add_argument(
        '--no-isolation',
        '-n',
        action='store_true',
        help='do not isolate the build in a virtual environment',
        default=not default_isolation.enabled,
    )
    group.add_argument(
        '--ensurepip',
        dest='ensure_pip',
        action='store_true',
        help='isolate in a virtual environment and call a fresh ensurepip every time',
        default=default_isolation.ensure_pip,
    )
    group.add_argument(
        '--cache',
        dest='cache',
        help='cache isolation environment(s) in between runs',
        default=default_isolation.cache,
    )
    group.add_argument(
        '--reset-cache',
        dest='reset_cache',
        help='clear out the tools cache',
        action='store_true',
        default=default_isolation.reset_cache,
    )
    return parser


def config_setting(arg):
    split_data = arg.split('=')
    data = [split_data[0], '='.join(split_data[1:])]
    setting = data[0]
    value = data[1] if len(data) >= 2 else ''
    return setting, value


def main(cli_args, prog=None):  # type: (List[str], Optional[str]) -> None
    """
    Parses the CLI arguments and invokes the build process.

    :param cli_args: CLI arguments
    :param prog: name of the program
    """
    parser = main_parser()
    if prog:
        parser.prog = prog
    args = parser.parse_args(cli_args)

    conf = defaultdict(list)
    for key, value in args.config_setting:
        conf[key].append(value)
    config_settings = {k: v[0] if len(v) == 1 else v for k, v in conf.items()}

    distributions = []
    if args.sdist:
        distributions.append('sdist')
    if args.wheel:
        distributions.append('wheel')
    if not distributions:
        distributions = ['sdist', 'wheel']

    isolation = Isolation(
        enabled=args.no_isolation is False,
        ensure_pip=args.ensure_pip,
        cache=args.cache,
        reset_cache=args.reset_cache,
    )
    build(args.srcdir, args.outdir, distributions, isolation, config_settings, args.skip_dependencies)


def entrypoint():  # type: () -> None
    main(sys.argv[1:])


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:], 'python -m build')
