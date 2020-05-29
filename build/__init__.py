# SPDX-License-Identifier: MIT

'''
python-build - A simple, correct PEP517 package builder
'''
__version__ = '0.0.2'

import importlib
import os
import sys

try:
    from importlib import metadata as importlib_metadata
except ImportError:
    import importlib_metadata  # type: ignore

from typing import List

import pep517.wrappers
import toml

if sys.version_info < (3,):
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
    import packaging.requirements

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

    metadata_extras = metadata.get_all('Provides-Extra') or []
    for extra in req.extras:
        if extra not in metadata_extras:
            return False

    if req.specifier:
        return req.specifier.contains(version)

    return True


class ProjectBuilder(object):
    def __init__(self, srcdir='.'):  # type: (str) -> None
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
            self._backend = self._build_system['build-backend']
        except KeyError:
            self._build_system = {
                'requires': [
                    'setuptools >= 40.8.0',
                    'wheel'
                ]
            }
            self._backend = 'setuptools.build_meta:__legacy__'

        try:
            importlib.import_module(self._backend.split(':')[0])
        except ImportError:
            raise BuildException("Backend '{}' is not available".format(self._backend))

        self.hook = pep517.wrappers.Pep517HookCaller(self.srcdir, self._backend,
                                                     backend_path=self._build_system.get('backend-path'))

    def check_depencencies(self, distribution):  # type: (str) -> List[str]
        '''
        Returns a set of the missing dependencies
        '''
        get_requires = getattr(self.hook, 'get_requires_for_build_{}'.format(distribution))

        dependencies = set()

        try:
            dependencies.update(get_requires())
        except pep517.wrappers.BackendUnavailable as e:
            raise e
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
        '''
        build = getattr(self.hook, 'build_{}'.format(distribution))

        try:
            build(outdir)
        except Exception as e:  # noqa: E722
            raise BuildBackendException('Backend operation failed: {}'.format(e))
