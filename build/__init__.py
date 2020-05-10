# SPDX-License-Identifier: MIT

'''
python-build - A simple, correct PEP517 package builder
'''
__version__ = '0.0.1'

import importlib
import os

from typing import List

import pep517.wrappers
import toml


class BuildException(Exception):
    pass


class BuildBackendException(Exception):
    pass


class ProjectBuilder(object):
    def __init__(self, srcdir='.'):  # type: (str) -> None
        self.srcdir = srcdir

        spec_file = os.path.join(srcdir, 'pyproject.toml')

        if not os.path.isfile(spec_file):
            raise BuildException(f'Missing project file: {spec_file}')

        with open(spec_file) as f:
            self._spec = toml.load(f)

        try:
            self._build_system = self._spec['build-system']
            self._backend = self._build_system['build-backend']
        except KeyError:
            raise BuildException('Missing backend definition in project file')

        try:
            importlib.import_module(self._backend)
        except ImportError:
            raise BuildException(f"Backend '{self._backend}' is not available")

        self.hook = pep517.wrappers.Pep517HookCaller(self.srcdir, self._backend,
                                                     backend_path=self._build_system.get('backend-path'))

    def check_depencencies(self, distribution):  # type: (str) -> List[str]
        '''
        Returns a set of the missing dependencies
        '''
        get_requires = getattr(self.hook, f'get_requires_for_build_{distribution}')

        dependencies = set()

        try:
            dependencies.update(get_requires())
        except pep517.wrappers.BackendUnavailable as e:
            raise e
        except Exception as e:  # noqa: E722
            raise BuildBackendException(f'Backend operation failed: {e}')

        missing = []
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)

        return missing

    def build(self, distribution, outdir):  # type: (str, str) -> None
        '''
        Builds a distribution
        '''
        build = getattr(self.hook, f'build_{distribution}')

        try:
            build(outdir)
        except Exception as e:  # noqa: E722
            raise BuildBackendException(f'Backend operation failed: {e}')
