# SPDX-License-Identifier: MIT

import argparse
import os
import sys
import traceback

from typing import List

from . import BuildBackendException, BuildException, ProjectBuilder


__all__ = ['build', 'main']


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


def build(srcdir, outdir, distributions, skip_dependencies=False):  # type: (str, str, List[str], bool) -> None
    '''
    Runs the build process

    :param srcdir: Source directory
    :param outdir: Output directory
    :param distributions: Distributions to build (sdist and/or wheel)
    :param skip_dependencies: Do not perform the dependency check
    '''
    try:
        builder = ProjectBuilder(srcdir)

        for dist in distributions:
            if not skip_dependencies:
                missing = builder.check_depencencies(dist)
                if missing:
                    _error('Missing dependencies:' + ''.join(['\n\t' + dep for dep in missing]))

            builder.build(dist, outdir)
    except BuildException as e:
        _error(str(e))
    except BuildBackendException as e:
        if sys.version_info >= (3, 5):  # pragma: no cover
            print(traceback.format_exc(-1))
        else:  # pragma: no cover
            print(traceback.format_exc())
        _error(str(e))


def main(cli_args):  # type: (List[str]) -> None
    '''
    Parses the CLI arguments and invokes the build process.

    :param cli_args: CLI arguments
    '''
    cwd = os.getcwd()
    out = os.path.join(cwd, 'dist')
    parser = argparse.ArgumentParser()
    parser.add_argument('srcdir',
                        type=str, nargs='?', metavar=cwd, default=cwd,
                        help='source directory (defaults to current directory)')
    parser.add_argument('--sdist', '-s',
                        action='store_true',
                        help='build a source package')
    parser.add_argument('--wheel', '-w',
                        action='store_true',
                        help='build a wheel')
    parser.add_argument('--outdir', '-o', metavar=out,
                        type=str, default=out,
                        help='output directory')
    parser.add_argument('--skip-dependencies', '-x',
                        action='store_true',
                        help='does not check for the dependencies')
    args = parser.parse_args(cli_args)

    distributions = []

    if args.sdist:
        distributions.append('sdist')
    if args.wheel:
        distributions.append('wheel')

    # default targets
    if not distributions:
        distributions = ['sdist', 'wheel']

    build(args.srcdir, args.outdir, distributions, args.skip_dependencies)


if __name__ == '__main__':  # pragma: no cover
    sys.argv[0] = 'python -m build'
    main(sys.argv[1:])
