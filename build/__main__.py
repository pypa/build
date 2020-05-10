# SPDX-License-Identifier: MIT

import argparse
import os
import sys
import traceback

from . import BuildException, BuildBackendException, ProjectBuilder


def _error(msg, code=1):  # type: (str, int) -> None
    prefix = 'ERROR'
    if sys.stdout.isatty():
        prefix = '\33[91m' + prefix + '\33[0m'
    print(prefix, msg)
    exit(code)


if __name__ == '__main__':  # noqa: C901
    cwd = os.getcwd()
    out = os.path.join(cwd, 'dist')
    parser = argparse.ArgumentParser()
    parser.add_argument('srcdir',
                        type=str, nargs='?', metavar=cwd, default=cwd,
                        help='source directory (defaults to current directory)')
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='enable verbose output')
    parser.add_argument('--sdist', '-s',
                        action='store_true',
                        help='build a source package')
    parser.add_argument('--wheel', '-w',
                        action='store_true',
                        help='build a wheel')
    parser.add_argument('--outdir', '-o', metavar=out,
                        type=str, default=out,
                        help='output directory')
    args = parser.parse_args()

    distributions = []

    if args.sdist:
        distributions.append('sdist')
    if args.wheel:
        distributions.append('wheel')

    # default targets
    if not distributions:
        distributions = ['sdist', 'wheel']

    try:
        builder = ProjectBuilder(args.srcdir)

        for dist in distributions:
            missing = builder.check_depencencies(dist)
            if missing:
                _error(f'Missing dependencies: {" ".join(missing)}')

            builder.build(dist, args.outdir)
    except BuildException as e:
        _error(str(e))
    except BuildBackendException as e:
        if sys.version_info >= (3, 5):
            print(traceback.format_exc(-1))
        else:
            print(traceback.format_exc())
        _error(str(e))
