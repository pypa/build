# SPDX-License-Identifier: MIT

import pytest

from build import BuildException, VersionChecker, VersionUnwrapper


def test_normalize():
    assert VersionChecker.normalize_version('1') == '1'
    assert VersionChecker.normalize_version('1.2') == '1.2'
    assert VersionChecker.normalize_version('1.2.3') == '1.2.3'
    assert VersionChecker.normalize_version('1.2.3.4') == '1.2.3.4'
    assert VersionChecker.normalize_version('1.2.3.4.5') == '1.2.3.4.5'
    assert VersionChecker.normalize_version('1.2.3.4.5.6') == '1.2.3.4.5.6'
    assert VersionChecker.normalize_version('1.0RC1') == '1.0rc1'
    assert VersionChecker.normalize_version('v1.0RC1') == '1.0rc1'
    assert VersionChecker.normalize_version('V1.0RC1') == '1.0rc1'
    assert VersionChecker.normalize_version('000.000.000') == '0.0.0'
    assert VersionChecker.normalize_version('0001.0002.0003') == '1.2.3'
    assert VersionChecker.normalize_version('2020.2') == '2020.2'

    assert VersionChecker.normalize_version('1.0a') == '1.0a0'
    assert VersionChecker.normalize_version('1.0003a') == '1.3a0'
    assert VersionChecker.normalize_version('1.000123a') == '1.123a0'
    assert VersionChecker.normalize_version('1.0.a0') == '1.0a0'
    assert VersionChecker.normalize_version('1.0.a') == '1.0a0'
    assert VersionChecker.normalize_version('1.0-a') == '1.0a0'
    assert VersionChecker.normalize_version('1.0_a') == '1.0a0'

    assert VersionChecker.normalize_version('1.0alpha3') == '1.0a3'
    assert VersionChecker.normalize_version('1.0alpha') == '1.0a0'
    assert VersionChecker.normalize_version('1.0003alpha') == '1.3a0'
    assert VersionChecker.normalize_version('1.000123alpha') == '1.123a0'
    assert VersionChecker.normalize_version('1.0.alpha0') == '1.0a0'
    assert VersionChecker.normalize_version('1.0.alpha') == '1.0a0'
    assert VersionChecker.normalize_version('1.0-alpha') == '1.0a0'
    assert VersionChecker.normalize_version('1.0_alpha') == '1.0a0'

    assert VersionChecker.normalize_version('1.0beta3') == '1.0b3'
    assert VersionChecker.normalize_version('1.0beta') == '1.0b0'
    assert VersionChecker.normalize_version('1.0003beta') == '1.3b0'
    assert VersionChecker.normalize_version('1.000123beta') == '1.123b0'
    assert VersionChecker.normalize_version('1.0.beta0') == '1.0b0'
    assert VersionChecker.normalize_version('1.0.beta') == '1.0b0'
    assert VersionChecker.normalize_version('1.0-beta') == '1.0b0'
    assert VersionChecker.normalize_version('1.0_beta') == '1.0b0'

    assert VersionChecker.normalize_version('1.0b3') == '1.0b3'
    assert VersionChecker.normalize_version('1.0b') == '1.0b0'
    assert VersionChecker.normalize_version('1.0003b') == '1.3b0'
    assert VersionChecker.normalize_version('1.000123b') == '1.123b0'
    assert VersionChecker.normalize_version('1.0.b0') == '1.0b0'
    assert VersionChecker.normalize_version('1.0.b') == '1.0b0'
    assert VersionChecker.normalize_version('1.0-b') == '1.0b0'
    assert VersionChecker.normalize_version('1.0_b') == '1.0b0'

    assert VersionChecker.normalize_version('1.0c3') == '1.0rc3'
    assert VersionChecker.normalize_version('1.0c') == '1.0rc0'
    assert VersionChecker.normalize_version('1.0003c') == '1.3rc0'
    assert VersionChecker.normalize_version('1.000123c') == '1.123rc0'
    assert VersionChecker.normalize_version('1.0.c0') == '1.0rc0'
    assert VersionChecker.normalize_version('1.0.c') == '1.0rc0'
    assert VersionChecker.normalize_version('1.0-c') == '1.0rc0'
    assert VersionChecker.normalize_version('1.0_c') == '1.0rc0'

    assert VersionChecker.normalize_version('1.0r3') == '1.0.post3'
    assert VersionChecker.normalize_version('1.0r') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0003r') == '1.3.post0'
    assert VersionChecker.normalize_version('1.000123r') == '1.123.post0'
    assert VersionChecker.normalize_version('1.0.r0') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0.r') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0-r') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0_r') == '1.0.post0'

    assert VersionChecker.normalize_version('1.0rev3') == '1.0.post3'
    assert VersionChecker.normalize_version('1.0rev') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0003rev') == '1.3.post0'
    assert VersionChecker.normalize_version('1.000123rev') == '1.123.post0'
    assert VersionChecker.normalize_version('1.0.rev0') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0.rev') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0-rev') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0_rev') == '1.0.post0'

    assert VersionChecker.normalize_version('1.0post3') == '1.0.post3'
    assert VersionChecker.normalize_version('1.0post') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0003post') == '1.3.post0'
    assert VersionChecker.normalize_version('1.000123post') == '1.123.post0'
    assert VersionChecker.normalize_version('1.0.post0') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0.post') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0-post') == '1.0.post0'
    assert VersionChecker.normalize_version('1.0_post') == '1.0.post0'

    assert VersionChecker.normalize_version('1.0dev3') == '1.0dev3'
    assert VersionChecker.normalize_version('1.0dev') == '1.0dev0'
    assert VersionChecker.normalize_version('1.0003dev') == '1.3dev0'
    assert VersionChecker.normalize_version('1.000123dev') == '1.123dev0'
    assert VersionChecker.normalize_version('1.0.dev0') == '1.0dev0'
    assert VersionChecker.normalize_version('1.0.dev') == '1.0dev0'
    assert VersionChecker.normalize_version('1.0-dev') == '1.0dev0'
    assert VersionChecker.normalize_version('1.0_dev') == '1.0dev0'

    assert VersionChecker.normalize_version('1.0+foo3') == '1.0+foo3'
    assert VersionChecker.normalize_version('1.0+foo') == '1.0+foo'
    assert VersionChecker.normalize_version('1.0003+foo') == '1.3+foo'
    assert VersionChecker.normalize_version('1.000123+foo') == '1.123+foo'
    assert VersionChecker.normalize_version('1.0+foo0') == '1.0+foo0'
    assert VersionChecker.normalize_version('1.0+foo.1') == '1.0+foo.1'
    assert VersionChecker.normalize_version('1.0+foo-1') == '1.0+foo.1'
    assert VersionChecker.normalize_version('1.0+foo_1') == '1.0+foo.1'


def test_version_compare():
    a = VersionUnwrapper('1')
    b = VersionUnwrapper('1.1')
    c = VersionUnwrapper('1.1.1')

    assert a.cmp('==', a) is True
    assert b.cmp('==', b) is True
    assert c.cmp('==', c) is True

    a = VersionUnwrapper('1.1.post1')

    assert a.cmp('==', VersionUnwrapper('1.1')) is False
    assert a.cmp('==', VersionUnwrapper('1.1.post1')) is True
    assert a.cmp('==', VersionUnwrapper('1.1.*')) is True

    assert a.cmp('!=', VersionUnwrapper('1.1')) is True
    assert a.cmp('!=', VersionUnwrapper('1.1.post1')) is False
    assert a.cmp('!=', VersionUnwrapper('1.1.*')) is False

    assert a.cmp('>=', VersionUnwrapper('2.1.post1')) is False
    assert a.cmp('>=', VersionUnwrapper('2.1')) is False
    assert a.cmp('>=', VersionUnwrapper('1.1.post1')) is True
    assert a.cmp('>=', VersionUnwrapper('1.1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1.post1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1')) is True

    assert a.cmp('>=', VersionUnwrapper('1.1a1')) is False
    assert a.cmp('>=', VersionUnwrapper('1.1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1a1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1')) is True

    a = VersionUnwrapper('1.1a1')

    assert a.cmp('==', VersionUnwrapper('1.1')) is False
    assert a.cmp('==', VersionUnwrapper('1.1a1')) is True
    assert a.cmp('==', VersionUnwrapper('1.1.*')) is True

    assert a.cmp('!=', VersionUnwrapper('1.1')) is True
    assert a.cmp('!=', VersionUnwrapper('1.1a1')) is False
    assert a.cmp('!=', VersionUnwrapper('1.1.*')) is False

    assert a.cmp('>=', VersionUnwrapper('1.1a1')) is True
    assert a.cmp('>=', VersionUnwrapper('1.1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1a1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1')) is True

    a = VersionUnwrapper('1.1')

    assert a.cmp('==', VersionUnwrapper('1.1')) is True
    assert a.cmp('==', VersionUnwrapper('1.1.0')) is True
    assert a.cmp('==', VersionUnwrapper('1.1.dev1')) is False
    assert a.cmp('==', VersionUnwrapper('1.1a1')) is False
    assert a.cmp('==', VersionUnwrapper('1.1.post1')) is False
    assert a.cmp('==', VersionUnwrapper('1.1.*')) is True

    assert a.cmp('!=', VersionUnwrapper('1.1')) is False
    assert a.cmp('!=', VersionUnwrapper('1.1.0')) is False
    assert a.cmp('!=', VersionUnwrapper('1.1.dev1')) is True
    assert a.cmp('!=', VersionUnwrapper('1.1a1')) is True
    assert a.cmp('!=', VersionUnwrapper('1.1.post1')) is True
    assert a.cmp('!=', VersionUnwrapper('1.1.*')) is False

    assert a.cmp('===', VersionUnwrapper('1.1')) is True
    assert a.cmp('===', VersionUnwrapper('1.1.0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1.0.0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1.0a0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1.0b0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1.0rc0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1.a0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1.b0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1.rc0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1.post0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1.dev0')) is False
    assert a.cmp('===', VersionUnwrapper('1.1+foo')) is False

    assert a.cmp('>=', VersionUnwrapper('2.1')) is False
    assert a.cmp('>=', VersionUnwrapper('2.1.0')) is False
    assert a.cmp('>=', VersionUnwrapper('1.1')) is True
    assert a.cmp('>=', VersionUnwrapper('1.1.0')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1.0')) is True
    assert a.cmp('>=', VersionUnwrapper('2.*')) is False
    assert a.cmp('>=', VersionUnwrapper('1.*')) is True
    assert a.cmp('>=', VersionUnwrapper('0.*')) is True
    assert a.cmp('>=', VersionUnwrapper('1.1a1')) is False
    assert a.cmp('>=', VersionUnwrapper('1.1b1')) is False
    assert a.cmp('>=', VersionUnwrapper('1.1rc1')) is False
    assert a.cmp('>=', VersionUnwrapper('1.1.post1')) is False
    assert a.cmp('>=', VersionUnwrapper('1.1.dev1')) is False

    with pytest.raises(BuildException):
        a.cmp('>=', VersionUnwrapper('1.1+foo'))
    with pytest.raises(BuildException):
        a.cmp('>=', VersionUnwrapper('0.1+foo'))

    assert a.cmp('<=', VersionUnwrapper('0.1')) is False
    assert a.cmp('<=', VersionUnwrapper('0.1.0')) is False
    assert a.cmp('<=', VersionUnwrapper('1.1')) is True
    assert a.cmp('<=', VersionUnwrapper('1.1.0')) is True
    assert a.cmp('<=', VersionUnwrapper('2.1')) is True
    assert a.cmp('<=', VersionUnwrapper('2.1.0')) is True
    assert a.cmp('<=', VersionUnwrapper('2.*')) is True
    assert a.cmp('<=', VersionUnwrapper('1.*')) is True
    assert a.cmp('<=', VersionUnwrapper('0.*')) is False
    assert a.cmp('<=', VersionUnwrapper('1.1a1')) is True
    assert a.cmp('<=', VersionUnwrapper('1.1b1')) is True
    assert a.cmp('<=', VersionUnwrapper('1.1rc1')) is True
    assert a.cmp('<=', VersionUnwrapper('1.1.post1')) is True
    assert a.cmp('<=', VersionUnwrapper('1.1.dev1')) is True

    with pytest.raises(BuildException):
        a.cmp('<=', VersionUnwrapper('1.1+foo'))
    with pytest.raises(BuildException):
        a.cmp('<=', VersionUnwrapper('0.1+foo'))

    assert a.cmp('>', VersionUnwrapper('2.1')) is False
    assert a.cmp('>', VersionUnwrapper('2.1.0')) is False
    assert a.cmp('>', VersionUnwrapper('1.1')) is False
    assert a.cmp('>', VersionUnwrapper('1.1.0')) is False
    assert a.cmp('>', VersionUnwrapper('0.1')) is True
    assert a.cmp('>', VersionUnwrapper('0.1.0')) is True
    assert a.cmp('>', VersionUnwrapper('2.*')) is False
    assert a.cmp('>', VersionUnwrapper('1.*')) is False
    assert a.cmp('>', VersionUnwrapper('0.*')) is True

    with pytest.raises(BuildException):
        a.cmp('>', VersionUnwrapper('1.1a1'))
    with pytest.raises(BuildException):
        a.cmp('>', VersionUnwrapper('1.1b1'))
    with pytest.raises(BuildException):
        a.cmp('>', VersionUnwrapper('1.1rc1'))
    with pytest.raises(BuildException):
        a.cmp('>', VersionUnwrapper('1.1.post1'))
    with pytest.raises(BuildException):
        a.cmp('>', VersionUnwrapper('1.1.dev1'))
    with pytest.raises(BuildException):
        a.cmp('>', VersionUnwrapper('1.1+foo'))
    with pytest.raises(BuildException):
        a.cmp('>', VersionUnwrapper('0.1+foo'))

    assert a.cmp('<', VersionUnwrapper('0.1')) is False
    assert a.cmp('<', VersionUnwrapper('0.1.0')) is False
    assert a.cmp('<', VersionUnwrapper('1.1')) is False
    assert a.cmp('<', VersionUnwrapper('1.1.0')) is False
    assert a.cmp('<', VersionUnwrapper('2.1')) is True
    assert a.cmp('<', VersionUnwrapper('2.1.0')) is True
    assert a.cmp('<', VersionUnwrapper('2.*')) is True
    assert a.cmp('<', VersionUnwrapper('1.*')) is False
    assert a.cmp('<', VersionUnwrapper('0.*')) is False

    with pytest.raises(BuildException):
        a.cmp('<', VersionUnwrapper('1.1a1'))
    with pytest.raises(BuildException):
        a.cmp('<', VersionUnwrapper('1.1b1'))
    with pytest.raises(BuildException):
        a.cmp('<', VersionUnwrapper('1.1rc1'))
    with pytest.raises(BuildException):
        a.cmp('<', VersionUnwrapper('1.1.post1'))
    with pytest.raises(BuildException):
        a.cmp('<', VersionUnwrapper('1.1.dev1'))
    with pytest.raises(BuildException):
        a.cmp('<', VersionUnwrapper('1.1+foo'))
    with pytest.raises(BuildException):
        a.cmp('<', VersionUnwrapper('0.1+foo'))


def test_version_requirements():
    assert VersionChecker.check_version('toml') is True
    assert VersionChecker.check_version('pep517') is True

    assert VersionChecker.check_version('toml>=0.1') is True
    assert VersionChecker.check_version('toml<=0.1') is False
    assert VersionChecker.check_version('toml>0.1') is True
    assert VersionChecker.check_version('toml<0.1') is False
    assert VersionChecker.check_version('toml==0.1') is False
    assert VersionChecker.check_version('toml~=0.1') is True
    assert VersionChecker.check_version('toml~=1.1') is False

    with pytest.raises(BuildException):
        VersionChecker.check_version('toml~=0.0+foo')
    with pytest.raises(BuildException):
        VersionChecker.check_version('toml~=0.000+foo')
    with pytest.raises(BuildException):
        VersionChecker.check_version('toml~=0.000123+foo')

    assert VersionChecker.check_version('toml~=0.1') == VersionChecker.check_version('toml >= 0.1, == 0.*')
    assert VersionChecker.check_version('toml~=0.1.2') == VersionChecker.check_version('toml >= 0.1.2, == 0.1.*')

    try:
        import requests  # noqa: F401
        assert VersionChecker.check_version('requests [security, socks] >= 2.8.1, == 2.8.* ; python_version < "2.7"') is True
        assert VersionChecker.check_version('requests [security, socks] >= 2.8.1, < 3.*') is True
    except ImportError:
        pass

    with pytest.raises(BuildException):
        VersionChecker.check_version('toml~=1')
    with pytest.raises(BuildException):
        VersionChecker.check_version('toml~=1.*')

    with pytest.raises(BuildException):
        VersionChecker.check_version('toml~=0+foo')
