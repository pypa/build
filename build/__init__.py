# SPDX-License-Identifier: MIT

'''
python-build - A simple, correct PEP517 package builder
'''
__version__ = '0.0.3.1'

import importlib
import os
import sys

from typing import List

import pep517.wrappers
import toml


if sys.version_info < (3,):  # pragma: no cover
    FileNotFoundError = IOError
    PermissionError = OSError


class BuildException(Exception):
    '''
    Exception raised by ProjectBuilder
    '''


class BuildBackendException(Exception):
    '''
    Exception raised when the backend fails
    '''


def check_version(requirement_string, extra=''):  # type: (str, str) -> bool
    '''
    :param requirement_string: Requirement string
    :param extra: Extra (eg. test in myproject[test])
    '''
    import packaging.requirements

    if sys.version_info >= (3, 8):  # pragma: no cover
        from importlib import metadata as importlib_metadata
    else:  # pragma: no cover
        import importlib_metadata

    req = packaging.requirements.Requirement(requirement_string)
    env = {
        'extra': extra
    }

    if req.marker and not req.marker.evaluate(env):
        return True

    try:
        version = importlib_metadata.version(req.name)
        metadata = importlib_metadata.metadata(req.name)
    except importlib_metadata.PackageNotFoundError:
        return False

    for extra in req.extras:
        if extra not in (metadata.get_all('Provides-Extra') or []):
            return False

    if req.specifier:
        return req.specifier.contains(version)

    return True


class ProjectBuilder(object):
    def __init__(self, srcdir='.'):  # type: (str) -> None
        '''
        :param srcdir: Source directory
        '''
        self.srcdir = srcdir

        spec_file = os.path.join(srcdir, 'pyproject.toml')

        try:
            with open(spec_file) as f:
                self._spec = toml.load(f)
        except FileNotFoundError:
            self._spec = {}
        except PermissionError as e:
            raise BuildException("{}: '{}' ".format(e.strerror, e.filename))

        try:
            self._build_system = self._spec['build-system']
        except KeyError:
            self._build_system = {
                'build-backend': 'setuptools.build_meta:__legacy__',
                'requires': [
                    'setuptools >= 40.8.0',
                    'wheel'
                ]
            }

        self._backend = self._build_system['build-backend']

        try:
            importlib.import_module(self._backend.split(':')[0])
        except ImportError:  # can't mock importlib.import_module  # pragma: no cover
            raise BuildException("Backend '{}' is not available".format(self._backend))

        self.hook = pep517.wrappers.Pep517HookCaller(self.srcdir, self._backend,
                                                     backend_path=self._build_system.get('backend-path'))

    def check_depencencies(self, distribution):  # type: (str) -> List[str]
        '''
        Returns a set of the missing dependencies

        :param distribution: Distribution to build (sdist or wheel)
        '''
        get_requires = getattr(self.hook, 'get_requires_for_build_{}'.format(distribution))

        dependencies = set()

        try:
            dependencies.update(get_requires())
        except Exception as e:  # noqa: E722
            raise BuildBackendException('Backend operation failed: {}'.format(e))

        missing = []
        for dep in dependencies:
            if not check_version(dep):
                missing.append(dep)

        return missing

    def build(self, distribution, outdir):  # type: (str, str) -> None
        '''
        Builds a distribution

        :param distribution: Distribution to build (sdist or wheel)
        :param outdir: Outpur directory
        '''
        build = getattr(self.hook, 'build_{}'.format(distribution))

        try:
            build(outdir)
        except Exception as e:  # noqa: E722
            raise BuildBackendException('Backend operation failed: {}'.format(e))
