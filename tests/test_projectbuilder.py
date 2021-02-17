# SPDX-License-Identifier: MIT

from __future__ import unicode_literals

import copy
import os
import sys
import textwrap
import typing

import pep517.wrappers
import pytest

import build


if sys.version_info >= (3, 8):  # pragma: no cover
    from importlib import metadata as importlib_metadata
else:  # pragma: no cover
    import importlib_metadata

if sys.version_info >= (3,):  # pragma: no cover
    build_open_owner = 'builtins'
else:  # pragma: no cover
    build_open_owner = 'build'
    FileNotFoundError = IOError
    PermissionError = OSError


DEFAULT_BACKEND = {
    'build-backend': 'setuptools.build_meta:__legacy__',
    'requires': ['setuptools >= 40.8.0', 'wheel'],
}


class MockDistribution(importlib_metadata.Distribution):
    def locate_file(self, path):  # pragma: no cover
        return ''

    @classmethod
    def from_name(cls, name):
        if name == 'extras_dep':
            return ExtraMockDistribution()
        elif name == 'requireless_dep':
            return RequirelessMockDistribution()
        elif name == 'recursive_dep':
            return RecursiveMockDistribution()
        elif name == 'prerelease_dep':
            return PrereleaseMockDistribution()
        raise importlib_metadata.PackageNotFoundError


class ExtraMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return """
Metadata-Version: 2.2
Name: extras_dep
Version: 1.0.0
Provides-Extra: extra_without_associated_deps
Provides-Extra: extra_with_unmet_deps
Requires-Dist: unmet_dep; extra == 'extra_with_unmet_deps'
Provides-Extra: extra_with_met_deps
Requires-Dist: extras_dep; extra == 'extra_with_met_deps'
Provides-Extra: recursive_extra_with_unmet_deps
Requires-Dist: recursive_dep; extra == 'recursive_extra_with_unmet_deps'
""".strip()


class RequirelessMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return """
Metadata-Version: 2.2
Name: requireless_dep
Version: 1.0.0
""".strip()


class RecursiveMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return """
Metadata-Version: 2.2
Name: recursive_dep
Version: 1.0.0
Requires-Dist: recursive_unmet_dep
""".strip()


class PrereleaseMockDistribution(MockDistribution):
    def read_text(self, filename):
        if filename == 'METADATA':
            return """
Metadata-Version: 2.2
Name: prerelease_dep
Version: 1.0.1a0
""".strip()


@pytest.mark.parametrize(
    ('requirement_string', 'expected'),
    [
        ('extras_dep', None),
        ('missing_dep', ('missing_dep',)),
        ('requireless_dep', None),
        ('extras_dep[undefined_extra]', None),
        # would the wheel builder filter this out?
        ('extras_dep[extra_without_associated_deps]', None),
        (
            'extras_dep[extra_with_unmet_deps]',
            ('extras_dep[extra_with_unmet_deps]', "unmet_dep; extra == 'extra_with_unmet_deps'"),
        ),
        (
            'extras_dep[recursive_extra_with_unmet_deps]',
            (
                'extras_dep[recursive_extra_with_unmet_deps]',
                "recursive_dep; extra == 'recursive_extra_with_unmet_deps'",
                'recursive_unmet_dep',
            ),
        ),
        ('extras_dep[extra_with_met_deps]', None),
        ('missing_dep; python_version>"10"', None),
        ('missing_dep; python_version<="1"', None),
        ('missing_dep; python_version>="1"', ('missing_dep; python_version>="1"',)),
        ('extras_dep == 1.0.0', None),
        ('extras_dep == 2.0.0', ('extras_dep == 2.0.0',)),
        ('extras_dep[extra_without_associated_deps] == 1.0.0', None),
        ('extras_dep[extra_without_associated_deps] == 2.0.0', ('extras_dep[extra_without_associated_deps] == 2.0.0',)),
        ('prerelease_dep >= 1.0.0', None),
    ],
)
def test_check_dependency(monkeypatch, requirement_string, expected):
    monkeypatch.setattr(importlib_metadata, 'Distribution', MockDistribution)
    assert next(build.check_dependency(requirement_string), None) == expected


def test_init(mocker, test_flit_path, legacy_path, test_no_permission, test_bad_syntax_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller')

    # correct flit pyproject.toml
    builder = build.ProjectBuilder(test_flit_path)
    pep517.wrappers.Pep517HookCaller.assert_called_with(
        test_flit_path, 'flit_core.buildapi', backend_path=None, python_executable=sys.executable, runner=builder._runner
    )
    pep517.wrappers.Pep517HookCaller.reset_mock()

    # custom python
    builder = build.ProjectBuilder(test_flit_path, python_executable='some-python')
    pep517.wrappers.Pep517HookCaller.assert_called_with(
        test_flit_path, 'flit_core.buildapi', backend_path=None, python_executable='some-python', runner=builder._runner
    )
    pep517.wrappers.Pep517HookCaller.reset_mock()

    # FileNotFoundError
    builder = build.ProjectBuilder(legacy_path)
    pep517.wrappers.Pep517HookCaller.assert_called_with(
        legacy_path,
        'setuptools.build_meta:__legacy__',
        backend_path=None,
        python_executable=sys.executable,
        runner=builder._runner,
    )

    # PermissionError
    if sys.version_info[0] != 2 and os.name != 'nt':  # can't correctly set the permissions required for this
        with pytest.raises(build.BuildException):
            build.ProjectBuilder(test_no_permission)

    # TomlDecodeError
    with pytest.raises(build.BuildException):
        build.ProjectBuilder(test_bad_syntax_path)


@pytest.mark.parametrize('value', [b'something', typing.Text('something_else')])
def test_python_executable(test_flit_path, value):
    builder = build.ProjectBuilder(test_flit_path)

    builder.python_executable = value
    assert builder.python_executable == value
    assert builder._hook.python_executable == value


@pytest.mark.parametrize('distribution', ['wheel', 'sdist'])
def test_get_dependencies_missing_backend(packages_path, distribution):
    bad_backend_path = os.path.join(packages_path, 'test-bad-backend')
    builder = build.ProjectBuilder(bad_backend_path)

    with pytest.raises(build.BuildException):
        builder.get_dependencies(distribution)


@pytest.mark.parametrize('distribution', ['wheel', 'sdist'])
def test_get_dependencies_missing_optional_hooks(test_optional_hooks_path, distribution):
    builder = build.ProjectBuilder(test_optional_hooks_path)

    assert builder.get_dependencies(distribution) == set()


@pytest.mark.parametrize('distribution', ['wheel', 'sdist'])
def test_build_missing_backend(packages_path, distribution, tmpdir):
    bad_backend_path = os.path.join(packages_path, 'test-bad-backend')
    builder = build.ProjectBuilder(bad_backend_path)

    with pytest.raises(build.BuildException):
        builder.build(distribution, str(tmpdir))


def test_check_dependencies(mocker, test_flit_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller.get_requires_for_build_sdist')
    mocker.patch('pep517.wrappers.Pep517HookCaller.get_requires_for_build_wheel')

    builder = build.ProjectBuilder(test_flit_path)

    side_effects = [
        [],
        ['something'],
        pep517.wrappers.BackendUnavailable,
    ]

    builder._hook.get_requires_for_build_sdist.side_effect = copy.copy(side_effects)
    builder._hook.get_requires_for_build_wheel.side_effect = copy.copy(side_effects)

    # requires = []
    assert builder.check_dependencies('sdist') == {('flit_core >=2,<3',)}
    assert builder.check_dependencies('wheel') == {('flit_core >=2,<3',)}

    # requires = ['something']
    assert builder.check_dependencies('sdist') == {('flit_core >=2,<3',), ('something',)}
    assert builder.check_dependencies('wheel') == {('flit_core >=2,<3',), ('something',)}

    # BackendUnavailable
    with pytest.raises(build.BuildBackendException):
        builder.check_dependencies('sdist')
    with pytest.raises(build.BuildBackendException):
        not builder.check_dependencies('wheel')


def test_working_directory(tmp_dir):
    assert os.path.realpath(os.curdir) != os.path.realpath(tmp_dir)
    with build._working_directory(tmp_dir):
        assert os.path.realpath(os.curdir) == os.path.realpath(tmp_dir)


def test_build(mocker, test_flit_path, tmp_dir):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)
    mocker.patch('build._working_directory', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)

    builder._hook.build_sdist.side_effect = ['dist.tar.gz', Exception]
    builder._hook.build_wheel.side_effect = ['dist.whl', Exception]

    assert builder.build('sdist', tmp_dir) == os.path.join(tmp_dir, 'dist.tar.gz')
    builder._hook.build_sdist.assert_called_with(tmp_dir, None)
    build._working_directory.assert_called_with(test_flit_path)

    assert builder.build('wheel', tmp_dir) == os.path.join(tmp_dir, 'dist.whl')
    builder._hook.build_wheel.assert_called_with(tmp_dir, None)
    build._working_directory.assert_called_with(test_flit_path)

    with pytest.raises(build.BuildBackendException):
        build._working_directory.assert_called_with(test_flit_path)
        builder.build('sdist', tmp_dir)

    with pytest.raises(build.BuildBackendException):
        build._working_directory.assert_called_with(test_flit_path)
        builder.build('wheel', tmp_dir)


def test_default_backend(mocker, legacy_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(legacy_path)

    assert builder._build_system == DEFAULT_BACKEND


def test_missing_backend(mocker, test_no_backend_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_no_backend_path)

    assert builder._build_system == {'requires': [], 'build-backend': DEFAULT_BACKEND['build-backend']}


def test_missing_requires(mocker, test_no_requires_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    with pytest.raises(build.BuildException):
        build.ProjectBuilder(test_no_requires_path)


def test_build_system_typo(mocker, test_typo):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    with pytest.warns(build.TypoWarning):
        build.ProjectBuilder(test_typo)


def test_missing_outdir(mocker, tmp_dir, test_flit_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)
    builder._hook.build_sdist.return_value = 'dist.tar.gz'
    out = os.path.join(tmp_dir, 'out')

    builder.build('sdist', out)

    assert os.path.isdir(out)


def test_relative_outdir(mocker, tmp_dir, test_flit_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)
    builder._hook.build_sdist.return_value = 'dist.tar.gz'

    builder.build('sdist', '.')

    builder._hook.build_sdist.assert_called_with(os.path.abspath('.'), None)


def test_build_not_dir_outdir(mocker, tmp_dir, test_flit_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)
    builder._hook.build_sdist.return_value = 'dist.tar.gz'
    out = os.path.join(tmp_dir, 'out')

    open(out, 'a').close()  # create empty file

    with pytest.raises(build.BuildException):
        builder.build('sdist', out)


@pytest.fixture(scope='session')
def demo_pkg_inline(tmp_path_factory):
    # builds a wheel without any dependencies and with a console script demo-pkg-inline
    tmp_path = tmp_path_factory.mktemp('demo-pkg-inline')
    builder = build.ProjectBuilder(srcdir=os.path.join(os.path.dirname(__file__), 'packages', 'inline'))
    out = tmp_path / 'dist'
    builder.build('wheel', str(out))
    return next(out.iterdir())


@pytest.mark.isolated
def test_build_with_dep_on_console_script(tmp_path, demo_pkg_inline, capfd, mocker):
    """
    All command-line scripts provided by the build-required packages must be present in the build environment's PATH.
    """
    # we first install demo pkg inline as build dependency (as this provides a console script we can check)
    # to validate backend invocations contain the correct path we use an inline backend that will fail, but first
    # provides the PATH information (and validates shutil.which is able to discover the executable - as PEP states)
    toml = '[build-system]\nrequires = ["demo_pkg_inline"]\nbuild-backend = "build"\nbackend-path = ["."]\n'
    code = textwrap.dedent(
        '''
        import os
        import sys
        print("BB " + os.environ["PATH"])
        if sys.version_info[0] == 3:
            import shutil
            exe_at = shutil.which("demo-pkg-inline")
        else:
            paths = os.environ["PATH"].split(os.pathsep)
            exe_at = os.path.join(paths[0], "demo-pkg-inline{}".format(".exe" if sys.platform == "win32" else ""))
            if not os.path.exists(exe_at):
                exe_at = None
        print("BB " + exe_at)
        '''
    )
    (tmp_path / 'pyproject.toml').write_text(toml)
    (tmp_path / 'build.py').write_text(code)

    deps = {str(demo_pkg_inline)}  # we patch the requires demo_pkg_inline to refer to the wheel -> we don't need index
    mocker.patch('build.ProjectBuilder.build_dependencies', new_callable=mocker.PropertyMock, return_value=deps)
    from build.__main__ import main

    with pytest.raises(SystemExit):
        main(['--wheel', '--outdir', str(tmp_path / 'dist'), str(tmp_path)])

    out, err = capfd.readouterr()
    lines = [line[3:] for line in out.splitlines() if line.startswith('BB ')]  # filter for our markers
    path_vars = lines[0].split(os.pathsep)
    which_detected = lines[1]
    assert which_detected.startswith(path_vars[0]), out


def test_prepare(mocker, tmp_dir, test_flit_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)
    mocker.patch('build._working_directory', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)
    builder._hook.prepare_metadata_for_build_wheel.return_value = 'dist-1.0.dist-info'

    assert builder.prepare('wheel', tmp_dir) == os.path.join(tmp_dir, 'dist-1.0.dist-info')
    builder._hook.prepare_metadata_for_build_wheel.assert_called_with(tmp_dir, None, _allow_fallback=False)
    build._working_directory.assert_called_with(test_flit_path)


def test_prepare_no_hook(mocker, tmp_dir, test_flit_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)
    failure = pep517.wrappers.HookMissing('prepare_metadata_for_build_wheel')
    builder._hook.prepare_metadata_for_build_wheel.side_effect = failure

    assert builder.prepare('wheel', tmp_dir) is None


def test_prepare_error(mocker, tmp_dir, test_flit_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)
    builder._hook.prepare_metadata_for_build_wheel.side_effect = Exception

    with pytest.raises(build.BuildBackendException, match='Backend operation failed: Exception'):
        builder.prepare('wheel', tmp_dir)


def test_prepare_not_dir_outdir(mocker, tmp_dir, test_flit_path):
    mocker.patch('pep517.wrappers.Pep517HookCaller', autospec=True)

    builder = build.ProjectBuilder(test_flit_path)

    out = os.path.join(tmp_dir, 'out')
    with open(out, 'w') as f:
        f.write('Not a directory')
    with pytest.raises(build.BuildException, match='Build path .* exists and is not a directory'):
        builder.prepare('wheel', out)
