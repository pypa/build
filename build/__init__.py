# SPDX-License-Identifier: MIT

'''
python-build - A simple, correct PEP517 package builder
'''
__version__ = '0.0.1'

import importlib
import importlib_metadata
import os
import re
import sys

from typing import List

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

        if env:
            if fields[0] == 'python':
                version = [str(v) for v in sys.version_info[:3]]
        else:
            try:
                version = importlib_metadata.version(fields[0]).split('.')
            except importlib_metadata.PackageNotFoundError:
                return False

        if len(fields) == 0:
            return True

        i = 1
        while i < len(fields):
            target = fields[i + 1].split('.')
            lenght = len(version) if len(version) < len(target) else len(target)
            local_version = version[:lenght]
            try:
                op = getattr(local_version, '__{}__'.format(ops[fields[i]]))
                if not op(target[:lenght]):
                    return False
            except (AttributeError, KeyError, TypeError):
                raise BuildException("Operation '{}' (from '{}') not supported".format(fields[i], requirement_string))
            i += 2

        return True

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
            if not self.check_version(dep):
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
