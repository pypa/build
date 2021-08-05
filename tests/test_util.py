# SPDX-License-Identifier: MIT

import pytest

import build.util


@pytest.mark.parametrize('isolated', [False, True])
def test_wheel_metadata(test_setuptools_path, isolated):
    metadata = build.util.project_wheel_metadata(test_setuptools_path, isolated)

    assert metadata['name'] == 'test-setuptools'
    assert metadata['version'] == '1.0.0'


def test_wheel_metadata_isolation(test_flit_path):
    metadata = build.util.project_wheel_metadata(test_flit_path)

    assert metadata['name'] == 'test_flit'
    assert metadata['version'] == '1.0.0'

    with pytest.raises(
        build.BuildBackendException,
        match="Backend 'flit_core.buildapi' is not available.",
    ):
        build.util.project_wheel_metadata(test_flit_path, isolated=False)


def test_with_get_requires(test_metadata):
    metadata = build.util.project_wheel_metadata(test_metadata)

    assert metadata['name'] == 'test-metadata'
    assert str(metadata['version']) == '1.0.0'
    assert metadata['summary'] == 'hello!'
