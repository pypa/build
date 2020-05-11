# SPDX-License-Identifier: MIT

'''
python-build - A simple, correct PEP517 package builder
'''
__version__ = '0.0.1'

import importlib
import importlib_metadata
import os
import platform
import re

from typing import Callable, List

import pep517.wrappers
import toml


class BuildException(Exception):
    '''
    Exception raised by ProjectBuilder
    '''


class BuildBackendException(Exception):
    '''
    Exception raised when the backend fails
    '''


class VersionChecker(object):
    @classmethod
    def _compare_version_strings(cls, val1, val2, operation):  # type: (str, str, str) -> bool
        ops = {
            '<=': 'le',
            '>=': 'ge',
            '<': 'lt',
            '>': 'gt',
            '==': 'eq',
            '!=': 'ne',
        }

        # TODO: validate
        v1 = val1.split('.')
        v2 = val2.split('.')

        length = len(val1) if len(val1) < len(val2) else len(val2)

        v1 = v1[:length]
        v2 = v2[:length]

        try:
            op = getattr(v1, '__{}__'.format(ops[operation]))  # type: Callable[[List[str]], bool]
            return op(v2)
        except (AttributeError, KeyError, TypeError):
            raise BuildException("Operation '{}' (from '{} {} {}') not supported".format(operation, val1, operation, val2))

    @classmethod
    def check_version(cls, requirement_string, env=False):  # type: (str, bool) -> bool  # noqa: 901
        ops = {
            '<=': 'le',
            '>=': 'ge',
            '<': 'lt',
            '>': 'gt',
            '==': 'eq',
            '!=': 'ne',
        }

        reqs = requirement_string.split(';')

        if len(reqs) > 1:
            for req in reqs[:0:-1]:  # loop over conditions in reverse
                if not cls.check_version(req, env=True):
                    return True

        explode_req = re.compile('({})'.format('|'.join(ops.keys())))
        fields = explode_req.split(re.sub('[ \'"]', '', reqs[0].strip()))  # ['something, '>=', '0.3']

        if not fields or len(fields) % 2 == 0:  # ['something', '>=']
            raise BuildException('Invalid dependency string: {}'.format(requirement_string))

        name = fields[0]

        if env:
            if name == 'python_version':
                version = '.'.join(platform.python_version_tuple()[:2])
            else:
                raise BuildException('Invalid environment marker: {}'.format(name))
        else:
            try:
                version = importlib_metadata.version(name).split('.')
            except importlib_metadata.PackageNotFoundError:
                return False

        if len(fields) == 0:
            return True

        i = 1
        while i < len(fields):
            cls._compare_version_strings(version, fields[i + 1], fields[i])
            i += 2

        return True


class ProjectBuilder(object):
    def __init__(self, srcdir='.'):  # type: (str) -> None
        self.srcdir = srcdir

        spec_file = os.path.join(srcdir, 'pyproject.toml')

        if not os.path.isfile(spec_file):
            raise BuildException('Missing project file: {}'.format(spec_file))

        with open(spec_file) as f:
            self._spec = toml.load(f)

        try:
            self._build_system = self._spec['build-system']
            self._backend = self._build_system['build-backend']
        except KeyError:
            raise BuildException('Missing backend definition in project file')

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
            if not VersionChecker.check_version(dep):
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
