# SPDX-License-Identifier: MIT

import importlib.util
import sys
import subprocess

import pytest

import build.util


@pytest.mark.pypy3323bug
@pytest.mark.parametrize('isolated', [False, pytest.param(True, marks=[pytest.mark.network, pytest.mark.isolated])])
def test_wheel_metadata(package_test_setuptools, isolated):
    metadata = build.util.project_wheel_metadata(package_test_setuptools, isolated)

    # Setuptools < v69.0.3 (https://github.com/pypa/setuptools/pull/4159) normalized this to dashes
    assert metadata['name'].replace('-', '_') == 'test_setuptools'
    assert metadata['version'] == '1.0.0'
    assert isinstance(metadata.json, dict)


@pytest.mark.network
@pytest.mark.pypy3323bug
def test_wheel_metadata_isolation(package_test_flit):
    if importlib.util.find_spec('flit_core'):
        pytest.xfail('flit_core is available -- we want it missing!')  # pragma: no cover

    metadata = build.util.project_wheel_metadata(package_test_flit)

    assert metadata['name'] == 'test_flit'
    assert metadata['version'] == '1.0.0'
    assert isinstance(metadata.json, dict)

    with pytest.raises(
        build.BuildBackendException,
        match="Backend 'flit_core.buildapi' is not available.",
    ):
        build.util.project_wheel_metadata(package_test_flit, isolated=False)


@pytest.mark.network
@pytest.mark.pypy3323bug
def test_with_get_requires(package_test_metadata):
    metadata = build.util.project_wheel_metadata(package_test_metadata)

    # Setuptools < v69.0.3 (https://github.com/pypa/setuptools/pull/4159) normalized this to dashes
    assert metadata['name'].replace('-', '_') == 'test_metadata'
    assert str(metadata['version']) == '1.0.0'
    assert metadata['summary'] == 'hello!'
    assert isinstance(metadata.json, dict)


def test_current_environment_default():
    check_script = "import build.util, inspect; print(inspect.signature(build.util.project_wheel_metadata).parameters['isolated'].default)"
    cmd = [sys.executable, '-c', check_script]
    env = {'BUILD_ENVIRONMENT': 'current'}
    res = subprocess.check_output(cmd, env=env, text=True, encoding='utf-8')
    assert res.strip() == 'False'
