# SPDX-License-Identifier: MIT

'''
python-build - A simple, correct PEP517 package builder
'''
__version__ = '0.0.1'

import importlib
import itertools
import os
import platform
import re
import sys
import typing

try:
    from importlib import metadata as importlib_metadata
except ImportError:
    import importlib_metadata  # type: ignore

from typing import Iterable, List, Union

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


class VersionUnwrapper(object):
    def __init__(self, version_string):  # type: (str) -> None  # noqa: C901
        '''
        :param version_string: normalized version string
        '''
        self._version_string = version_string

        self._epoch = 0
        epoch_arr = version_string.split('!')
        if len(epoch_arr) == 2:
            version_string = epoch_arr[1]
            try:
                self._epoch = int(epoch_arr[0])
            except ValueError:
                raise BuildException('Invalid epoch: {}'.format(epoch_arr[0]))

        version_split = re.sub('([0-9])(a|b|rc|dev)([0-9])', r'\1.\2\3', version_string).split('+')
        self._version = typing.cast(List[Union[int, str]], version_split[0].split('.'))

        self._local = ''
        if len(version_split) > 1:
            self._local = version_split[1]

        self._check_len = len(self._version)
        self._alpha = False
        self._beta = False
        self._candidate = False
        self._post = False
        self._dev = False

        for i, part in enumerate(self._version):
            try:
                self._version[i] = int(part)
            except ValueError:
                assert isinstance(part, str)
                if part == '*':
                    self._check_len = i if i < self._check_len else self._check_len
                elif part.startswith('a'):
                    self._alpha = True
                elif part.startswith('b'):
                    self._beta = True
                elif part.startswith('rc'):
                    self._candidate = True
                elif part.startswith('post'):
                    self._post = True
                elif part.startswith('dev'):
                    self._dev = True
                else:
                    raise BuildException('Invalid version string: {}'.format(version_string))

    def __str__(self):  # type: () -> str
        return self._version_string

    def __repr__(self):  # type: () -> str
        return 'VersionUnwrapper({})'.format(self._version_string)

    def __iter__(self):  # type: () -> Iterable[Union[int, str]]
        return typing.cast(Iterable[Union[int, str]], iter([self.epoch] + self._version))

    def cmp(self, operation, val):
        return self.op(operation, self, val)

    @property
    def alpha(self):  # type: () -> bool
        return self._alpha

    @property
    def beta(self):  # type: () -> bool
        return self._beta

    @property
    def candidate(self):  # type: () -> bool
        return self._candidate

    @property
    def pre(self):  # type: () -> bool
        return self._alpha or self._beta or self._candidate

    @property
    def post(self):  # type: () -> bool
        return self._post

    @property
    def dev(self):  # type: () -> bool
        return self._dev

    @property
    def local(self):  # type: () -> str
        return self._local

    @property
    def epoch(self):  # type: () -> int
        return self._epoch

    @classmethod
    def op(cls, operation, current, base):  # type: (str, VersionUnwrapper, VersionUnwrapper) -> bool  # noqa: C901
        if sys.version_info < (3,):
            zip_longest = itertools.izip_longest
        else:
            zip_longest = itertools.zip_longest
        special_regex = re.compile(r'^([a-zA-Z]*)([0-9]+)')  # 'dev10' -> 'dev' '10'

        # https://www.python.org/dev/peps/pep-0440/#version-specifiers
        if operation == '==':
            for a, b in zip_longest(current, base, fillvalue=0):  # type: ignore
                if b == '*':
                    return True
                elif a != b:
                    return False
            if base.local:
                return current.local == base.local
            return True

        if operation == '>=':
            if base.local or current.local:
                raise BuildException('Invalid operation on local version: {} (in {} {} {})'.format(
                                     operation, current, operation, base))
            for a, b in zip_longest(current, base, fillvalue=0):  # type: ignore
                if isinstance(b, str) and b == '*':
                    return True
                special_a, num_a = special_regex.match(str(a)).groups()  # type: ignore
                special_b, num_b = special_regex.match(str(b)).groups()  # type: ignore
                if bool(special_a) ^ bool(special_b):  # one of them is special (alpha, beta, candidate, etc.)
                    return bool(special_a)
                if special_a != special_b:
                    return False
                if num_a == num_b:
                    continue
                return int(num_a) >= int(num_b)
            return True

        if operation == '<=':
            if base.local or current.local:
                raise BuildException('Invalid operation on local version: {} (in {} {} {})'.format(
                                     operation, current, operation, base))
            for a, b in zip_longest(current, base, fillvalue=0):  # type: ignore
                if isinstance(b, str) and b == '*':
                    return True
                special_a, num_a = special_regex.match(str(a)).groups()  # type: ignore
                special_b, num_b = special_regex.match(str(b)).groups()  # type: ignore
                if bool(special_a) ^ bool(special_b):  # one of them is special (alpha, beta, candidate, etc.)
                    return bool(special_b)
                if special_a != special_b:
                    return False
                if not int(num_a) <= int(num_b):
                    return False
            return True

        if operation == '>':
            if base.local or base.pre or base.post or base.dev or current.local or current.pre or current.post or current.dev:
                raise BuildException('Invalid operation on local or pre-release version: {} (in {} {} {})'.format(
                                     operation, current, operation, base))
            for a, b in zip_longest(current, base, fillvalue=0):  # type: ignore
                if isinstance(b, str) and b == '*':
                    return False
                a, b = int(a), int(b)
                if a < b:
                    return False
                if a > b:
                    return True
            return False

        if operation == '<':
            if base.local or base.pre or base.post or base.dev or current.local or current.pre or current.post or current.dev:
                raise BuildException('Invalid operation on local or pre-release version: {} (in {} {} {})'.format(
                                     operation, current, operation, base))
            for a, b in zip_longest(current, base, fillvalue=0):  # type: ignore
                if isinstance(b, str) and b == '*':
                    return False
                a, b = int(a), int(b)
                if a > b:
                    return False
                if a < b:
                    return True
            return False

        elif operation == '!=':
            return not cls.op('==', current, base)

        elif operation == '===':
            return str(base) == str(current)  # type: ignore

        elif operation == '~=':
            if base.local or current.local:
                raise BuildException('Invalid operation on local version: {} (in {} {} {})'.format(
                                     operation, current, operation, base))
            arb_ver = list(base)[1:]  # type: ignore
            if len(arb_ver) <= 1 or arb_ver[1] == '*':
                raise BuildException("Invalid operation '{}' against value '{}'".format(operation, base))
            arb_ver[-1] = '*'
            return (
                cls.op('>=', current, base) and
                cls.op('==', current, VersionUnwrapper('.'.join([str(part) for part in arb_ver])))
            )

        else:
            raise BuildException('Invalid operation: {}'.format(operation))


class VersionChecker(object):
    @classmethod
    def normalize_version(cls, version):  # type: (str) -> str
        '''
        Normalizes version strings

        It follows the PEP440 specification
        https://www.python.org/dev/peps/pep-0440/#normalization
        '''
        # > All ascii letters should be interpreted case insensitively within a version and the normal form is lowercase
        version = version.strip().lower()

        # > In order to support the common version notation of v1.0 versions may be preceded by a single literal v character.
        # > This character MUST be ignored for all purposes and should be omitted from all normalized forms of the version.
        version = re.sub('^v', '', version)

        # > {Pre,Post, Development} releases should allow a ., -, or _ separator between the release segment and the
        # > {pre,post,development} release segment.
        version = re.sub(r'([0-9])(\.|-|_)(a|b|c|rc|r|alpha|beta|pre|preview|post|rev|dev)', r'\1\3', version)

        # > Pre-releases allow the additional spellings of alpha, beta, c, pre, and preview
        # > for a, b, rc, rc, and rc respectively.
        version = re.sub(r'(\.[0-9]+)alpha([0-9]+|$|\.)', r'\1a\2', version)
        version = re.sub(r'(\.[0-9]+)beta([0-9]+|$|\.)', r'\1b\2', version)
        version = re.sub(r'(\.[0-9]+)(c|pre|preview)([0-9]+|$|\.)', r'\1rc\3', version)

        # > Post-releases allow the additional spellings of rev and r.
        version = re.sub(r'(\.[0-9]+|\.)(r|rev)([0-9]+|$|\.)', r'\1post\3', version)

        # > The normal form of this is with the . separator.
        version = re.sub(r'(\.[0-9]+)post([0-9]+|$|\.)', r'\1.post\2', version)

        # > The developmental release segment consists of the string .dev, followed by a non-negative integer value.
        version = re.sub(r'(\.[0-9]+)dev([0-9]+|$|\.)', r'\1.dev\2', version)

        # > {Pre,Post,Development} releases allow omitting the numeral in which case it is implicitly assumed to be 0.
        version = re.sub(r'(a|b|rc|post|dev)($|\.)', r'\g<1>0\2',
                         version)  # we use the \g<n> notation because \10 will evaluate to group 10

        # > This means that an integer version of 00 would normalize to 0 while 09000 would normalize to 9000.
        version = re.sub(r'(^|\.|a|b|c|rc|post|dev)(0+)([0-9])', r'\1\3', version)

        # > With a local version, in addition to the use of . as a separator of segments,
        # > the use of - and _ is also acceptable.
        version = re.sub(r'(\+[a-zA-Z]+)(-|_)([0-9]+)', r'\1.\3', version)

        # >Post releases allow omitting the post signifier all together.
        # > When using this form the separator MUST be - and no other form is allowed.
        version = re.sub(r'-([0-9]+)', r'.post\1', version)

        # > If no explicit epoch is given, the implicit epoch is 0.
        # the spec does not say that a 0 epoch should be removed from a normalized version but this seem to be the standard
        version = re.sub(r'^0+!', '', version)

        return version

    @classmethod
    def check_version(cls, requirement_string, env=False):  # type: (str, bool) -> bool  # noqa: 901
        ops = ['===', '~=', '<=', '>=', '<', '>', '==', '!=']

        reqs = requirement_string.split(';')

        if not env and len(reqs) > 1:
            for req in reqs[1:]:  # loop over environment markers
                if not cls.check_version(req, env=True):
                    return True

        explode_req = re.compile('({})'.format('|'.join(ops)))
        fields = explode_req.split(re.sub('[ \'"]', '', reqs[0].strip()))  # ['something, '>=', '0.3']

        if not fields or len(fields) % 2 == 0:  # ['something', '>=']
            raise BuildException('Invalid dependency string: {}'.format(requirement_string))

        name = fields[0].strip()

        if env:  # https://www.python.org/dev/peps/pep-0508/#environment-markers
            if name == 'os_name':
                version = os.name
            elif name == 'sys_platform':
                version = sys.platform
            elif name == 'platform_machine':
                version = platform.machine()
            elif name == 'platform_python_implementation':
                version = platform.python_implementation()
            elif name == 'platform_release':
                version = platform.release()
            elif name == 'platform_system':
                version = platform.system()
            elif name == 'platform_version':
                version == platform.version()
            elif name == 'python_version':
                version = '.'.join(platform.python_version_tuple()[:2])
            elif name == 'python_full_version':
                version = platform.python_version()
            elif name == 'implementation_name' and sys.version_info >= (3,):
                version = sys.implementation.name
            elif name == 'implementation_version':
                if hasattr(sys, 'implementation') and sys.version_info >= (3,):
                    info = sys.implementation.version
                    version = '{0.major}.{0.minor}.{0.micro}'.format(info)
                    kind = info.releaselevel
                    if kind != 'final':
                        version += kind[0] + str(info.serial)
                else:
                    version = '0'
            else:
                raise BuildException('Invalid environment marker: {}'.format(name))
        else:  # normal python package
            explode_extras = re.compile('(\\[.*\\])')
            # name_exploded: 'requests[security,socks]' -> ['requests', '[security,socks]']
            name_exploded = [part for part in explode_extras.split(name) if part]
            name = name_exploded[0]
            extras = []
            if len(name_exploded) == 2:
                extras = name_exploded[1].strip(' []').replace(' ', '').split(',')  # ['security' 'socks']
            elif len(name_exploded) > 2:  # ['requests', '[security,socks]', '[something,invalid]']
                raise BuildException('Invalid dependency name: {}'.format(name))
            try:
                version = importlib_metadata.version(name)
                metadata = importlib_metadata.metadata(name)
                for extra in extras:
                    if extra not in metadata.get_all('Provides-Extra'):
                        return False
            except importlib_metadata.PackageNotFoundError:
                return False

        if len(fields) == 0:
            return True

        i = 1
        while i < len(fields):
            if not VersionUnwrapper.op(fields[i], VersionUnwrapper(version), VersionUnwrapper(fields[i + 1].strip(' ,'))):
                return False
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
