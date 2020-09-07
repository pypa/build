# SPDX-License-Identifier: MIT

import os
import os.path
import re
import subprocess

import pytest

import build.__main__


_SDIST = re.compile('.*.tar.gz')
_WHEEL = re.compile('.*.whl')


@pytest.mark.parametrize(
    ('project'),
    [
        'python-build',
        'pip',
        'dateutil',
        'Solaar',
        os.path.join('flit', 'flit_core')
    ]
)
@pytest.mark.parametrize(
    ('args'),
    [
        [],
        ['-x', '--no-isolation'],
    ]
)
@pytest.mark.parametrize(
    ('call'),
    [
        None,  # via code
        ['python', '-m', 'build'],  # module
        ['python-build'],  # entrypoint
    ]
)
def test_build(tmp_dir, monkeypatch, integration_path, project, args, call):
    monkeypatch.setenv('SETUPTOOLS_SCM_PRETEND_VERSION', 'dummy')  # for the projects that use setuptools_scm

    if call and call[0] == 'python-build' and 'PYTHONPATH' in os.environ:
        pytest.skip('Running via PYTHONPATH, so the python-build entrypoint is not available')

    path = os.path.join(integration_path, project)
    args = [path, '-o', tmp_dir] + args

    if call is None:
        build.__main__.main(args)
    else:
        subprocess.check_call(call + args)

    assert filter(_SDIST.match, os.listdir(tmp_dir))
    assert filter(_WHEEL.match, os.listdir(tmp_dir))


def test_isolation(tmp_dir, test_flit_path, mocker):
    try:
        # if flit is available, we can't properly test the isolation - skip the test in those cases
        import flit_core  # noqa: F401
        pytest.xfail('flit_core is available')  # pragma: no cover
    except:  # noqa: E722
        pass

    mocker.patch('build.__main__._error')

    build.__main__.main([test_flit_path, '-o', tmp_dir, '--no-isolation'])
    build.__main__._error.assert_called_with("Backend 'flit_core.buildapi' is not available")
