# SPDX-License-Identifier: MIT

import importlib.util

import pytest

import build.util


@pytest.mark.pypy3323bug
@pytest.mark.parametrize('isolated', [False, pytest.param(True, marks=[pytest.mark.network, pytest.mark.isolated])])
def test_wheel_metadata(package_test_setuptools, isolated):
    metadata = build.util.project_wheel_metadata(package_test_setuptools, isolated)

    assert metadata['name'] == 'test-setuptools'
    assert metadata['version'] == '1.0.0'


@pytest.mark.network
@pytest.mark.pypy3323bug
def test_wheel_metadata_isolation(package_test_flit):
    if importlib.util.find_spec('flit_core'):
        pytest.xfail('flit_core is available -- we want it missing!')  # pragma: no cover

    metadata = build.util.project_wheel_metadata(package_test_flit)

    assert metadata['name'] == 'test_flit'
    assert metadata['version'] == '1.0.0'

    with pytest.raises(
        build.BuildBackendException,
        match="Backend 'flit_core.buildapi' is not available.",
    ):
        build.util.project_wheel_metadata(package_test_flit, isolated=False)


@pytest.mark.network
@pytest.mark.pypy3323bug
def test_with_get_requires(package_test_metadata):
    metadata = build.util.project_wheel_metadata(package_test_metadata)

    assert metadata['name'] == 'test-metadata'
    assert str(metadata['version']) == '1.0.0'
    assert metadata['summary'] == 'hello!'
