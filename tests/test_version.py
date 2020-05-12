# SPDX-License-Identifier: MIT

import pytest

from build import BuildException, VersionChecker, VersionUnwrapper


@pytest.mark.parametrize(
    ('version', 'normalized'),
    [
        # 1) packaging test cases
        # Various development release incarnations
        ('1.0dev', '1.0.dev0'),
        ('1.0.dev', '1.0.dev0'),
        ('1.0dev1', '1.0.dev1'),
        ('1.0dev', '1.0.dev0'),
        ('1.0-dev', '1.0.dev0'),
        ('1.0-dev1', '1.0.dev1'),
        ('1.0DEV', '1.0.dev0'),
        ('1.0.DEV', '1.0.dev0'),
        ('1.0DEV1', '1.0.dev1'),
        ('1.0DEV', '1.0.dev0'),
        ('1.0.DEV1', '1.0.dev1'),
        ('1.0-DEV', '1.0.dev0'),
        ('1.0-DEV1', '1.0.dev1'),
        # Various alpha incarnations
        ('1.0a', '1.0a0'),
        ('1.0.a', '1.0a0'),
        ('1.0.a1', '1.0a1'),
        ('1.0-a', '1.0a0'),
        ('1.0-a1', '1.0a1'),
        ('1.0alpha', '1.0a0'),
        ('1.0.alpha', '1.0a0'),
        ('1.0.alpha1', '1.0a1'),
        ('1.0-alpha', '1.0a0'),
        ('1.0-alpha1', '1.0a1'),
        ('1.0A', '1.0a0'),
        ('1.0.A', '1.0a0'),
        ('1.0.A1', '1.0a1'),
        ('1.0-A', '1.0a0'),
        ('1.0-A1', '1.0a1'),
        ('1.0ALPHA', '1.0a0'),
        ('1.0.ALPHA', '1.0a0'),
        ('1.0.ALPHA1', '1.0a1'),
        ('1.0-ALPHA', '1.0a0'),
        ('1.0-ALPHA1', '1.0a1'),
        # Various beta incarnations
        ('1.0b', '1.0b0'),
        ('1.0.b', '1.0b0'),
        ('1.0.b1', '1.0b1'),
        ('1.0-b', '1.0b0'),
        ('1.0-b1', '1.0b1'),
        ('1.0beta', '1.0b0'),
        ('1.0.beta', '1.0b0'),
        ('1.0.beta1', '1.0b1'),
        ('1.0-beta', '1.0b0'),
        ('1.0-beta1', '1.0b1'),
        ('1.0B', '1.0b0'),
        ('1.0.B', '1.0b0'),
        ('1.0.B1', '1.0b1'),
        ('1.0-B', '1.0b0'),
        ('1.0-B1', '1.0b1'),
        ('1.0BETA', '1.0b0'),
        ('1.0.BETA', '1.0b0'),
        ('1.0.BETA1', '1.0b1'),
        ('1.0-BETA', '1.0b0'),
        ('1.0-BETA1', '1.0b1'),
        # Various release candidate incarnations
        ('1.0c', '1.0rc0'),
        ('1.0.c', '1.0rc0'),
        ('1.0.c1', '1.0rc1'),
        ('1.0-c', '1.0rc0'),
        ('1.0-c1', '1.0rc1'),
        ('1.0rc', '1.0rc0'),
        ('1.0.rc', '1.0rc0'),
        ('1.0.rc1', '1.0rc1'),
        ('1.0-rc', '1.0rc0'),
        ('1.0-rc1', '1.0rc1'),
        ('1.0C', '1.0rc0'),
        ('1.0.C', '1.0rc0'),
        ('1.0.C1', '1.0rc1'),
        ('1.0-C', '1.0rc0'),
        ('1.0-C1', '1.0rc1'),
        ('1.0RC', '1.0rc0'),
        ('1.0.RC', '1.0rc0'),
        ('1.0.RC1', '1.0rc1'),
        ('1.0-RC', '1.0rc0'),
        ('1.0-RC1', '1.0rc1'),
        # Various post release incarnations
        ('1.0post', '1.0.post0'),
        ('1.0.post', '1.0.post0'),
        ('1.0post1', '1.0.post1'),
        ('1.0post', '1.0.post0'),
        ('1.0-post', '1.0.post0'),
        ('1.0-post1', '1.0.post1'),
        ('1.0POST', '1.0.post0'),
        ('1.0.POST', '1.0.post0'),
        ('1.0POST1', '1.0.post1'),
        ('1.0POST', '1.0.post0'),
        ('1.0r', '1.0.post0'),
        ('1.0rev', '1.0.post0'),
        ('1.0.POST1', '1.0.post1'),
        ('1.0.r1', '1.0.post1'),
        ('1.0.rev1', '1.0.post1'),
        ('1.0-POST', '1.0.post0'),
        ('1.0-POST1', '1.0.post1'),
        ('1.0-5', '1.0.post5'),
        ('1.0-r5', '1.0.post5'),
        ('1.0-rev5', '1.0.post5'),
        # Local version case insensitivity
        ('1.0+AbC', '1.0+abc'),
        # Integer Normalization
        ('1.01', '1.1'),
        ('1.0a05', '1.0a5'),
        ('1.0b07', '1.0b7'),
        ('1.0c056', '1.0rc56'),
        ('1.0rc09', '1.0rc9'),
        ('1.0.post000', '1.0.post0'),
        ('1.1.dev09000', '1.1.dev9000'),
        ('00!1.2', '1.2'),
        ('0100!0.0', '100!0.0'),
        # Various other normalizations
        ('v1.0', '1.0'),
        ('   v1.0\t\n', '1.0'),
        # 2) Our testcases
        ('1', '1'),
        ('1.2', '1.2'),
        ('1.2.3', '1.2.3'),
        ('1.2.3.4', '1.2.3.4'),
        ('1.2.3.4.5', '1.2.3.4.5'),
        ('1.2.3.4.5.6', '1.2.3.4.5.6'),
        ('1.0RC1', '1.0rc1'),
        ('v1.0RC1', '1.0rc1'),
        ('V1.0RC1', '1.0rc1'),
        ('000.000.000', '0.0.0'),
        ('0001.0002.0003', '1.2.3'),
        ('2020.2', '2020.2'),
        # alpha (a)
        ('1.0a', '1.0a0'),
        ('1.0003a', '1.3a0'),
        ('1.000123a', '1.123a0'),
        ('1.0.a0', '1.0a0'),
        ('1.0.a', '1.0a0'),
        ('1.0-a', '1.0a0'),
        ('1.0_a', '1.0a0'),
        # alpha
        ('1.0alpha3', '1.0a3'),
        ('1.0alpha', '1.0a0'),
        ('1.0003alpha', '1.3a0'),
        ('1.000123alpha', '1.123a0'),
        ('1.0.alpha0', '1.0a0'),
        ('1.0.alpha', '1.0a0'),
        ('1.0-alpha', '1.0a0'),
        ('1.0_alpha', '1.0a0'),
        # beta
        ('1.0beta3', '1.0b3'),
        ('1.0beta', '1.0b0'),
        ('1.0003beta', '1.3b0'),
        ('1.000123beta', '1.123b0'),
        ('1.0.beta0', '1.0b0'),
        ('1.0.beta', '1.0b0'),
        ('1.0-beta', '1.0b0'),
        ('1.0_beta', '1.0b0'),
        # beta (b)
        ('1.0b3', '1.0b3'),
        ('1.0b', '1.0b0'),
        ('1.0003b', '1.3b0'),
        ('1.000123b', '1.123b0'),
        ('1.0.b0', '1.0b0'),
        ('1.0.b', '1.0b0'),
        ('1.0-b', '1.0b0'),
        ('1.0_b', '1.0b0'),
        # release candidate (c)
        ('1.0c3', '1.0rc3'),
        ('1.0c', '1.0rc0'),
        ('1.0003c', '1.3rc0'),
        ('1.000123c', '1.123rc0'),
        ('1.0.c0', '1.0rc0'),
        ('1.0.c', '1.0rc0'),
        ('1.0-c', '1.0rc0'),
        ('1.0_c', '1.0rc0'),
        # post (r)
        ('1.0r3', '1.0.post3'),
        ('1.0r', '1.0.post0'),
        ('1.0003r', '1.3.post0'),
        ('1.000123r', '1.123.post0'),
        ('1.0.r0', '1.0.post0'),
        ('1.0.r', '1.0.post0'),
        ('1.0-r', '1.0.post0'),
        ('1.0_r', '1.0.post0'),
        # post (rev)
        ('1.0rev3', '1.0.post3'),
        ('1.0rev', '1.0.post0'),
        ('1.0003rev', '1.3.post0'),
        ('1.000123rev', '1.123.post0'),
        ('1.0.rev0', '1.0.post0'),
        ('1.0.rev', '1.0.post0'),
        ('1.0-rev', '1.0.post0'),
        ('1.0_rev', '1.0.post0'),
        # post
        ('1.0post3', '1.0.post3'),
        ('1.0post', '1.0.post0'),
        ('1.0003post', '1.3.post0'),
        ('1.000123post', '1.123.post0'),
        ('1.0.post0', '1.0.post0'),
        ('1.0.post', '1.0.post0'),
        ('1.0-post', '1.0.post0'),
        ('1.0_post', '1.0.post0'),
        # dev
        ('1.0dev3', '1.0.dev3'),
        ('1.0dev', '1.0.dev0'),
        ('1.0003dev', '1.3.dev0'),
        ('1.000123dev', '1.123.dev0'),
        ('1.0.dev0', '1.0.dev0'),
        ('1.0.dev', '1.0.dev0'),
        ('1.0-dev', '1.0.dev0'),
        ('1.0_dev', '1.0.dev0'),
        # local
        ('1.0+foo3', '1.0+foo3'),
        ('1.0+foo', '1.0+foo'),
        ('1.0003+foo', '1.3+foo'),
        ('1.000123+foo', '1.123+foo'),
        ('1.0+foo0', '1.0+foo0'),
        ('1.0+foo.1', '1.0+foo.1'),
        ('1.0+foo-1', '1.0+foo.1'),
        ('1.0+foo_1', '1.0+foo.1'),
    ],
)
def test_normalize(version, normalized):
    assert VersionChecker.normalize_version(version) == normalized


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
    assert a.cmp('==', VersionUnwrapper('0!1.1.*')) is True
    assert a.cmp('==', VersionUnwrapper('1!1.1.*')) is False

    assert a.cmp('!=', VersionUnwrapper('1.1')) is True
    assert a.cmp('!=', VersionUnwrapper('1.1.post1')) is False
    assert a.cmp('!=', VersionUnwrapper('1.1.*')) is False
    assert a.cmp('!=', VersionUnwrapper('0!1.1.*')) is False
    assert a.cmp('!=', VersionUnwrapper('1!1.1.*')) is True

    assert a.cmp('>=', VersionUnwrapper('2.1.post1')) is False
    assert a.cmp('>=', VersionUnwrapper('2.1')) is False
    assert a.cmp('>=', VersionUnwrapper('1.1.post1')) is True
    assert a.cmp('>=', VersionUnwrapper('1.1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1.post1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1')) is True
    assert a.cmp('>=', VersionUnwrapper('1!0.1.post1')) is False
    assert a.cmp('>=', VersionUnwrapper('1!0.1')) is False

    assert a.cmp('>=', VersionUnwrapper('1.1a1')) is False
    assert a.cmp('>=', VersionUnwrapper('1.1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1a1')) is True
    assert a.cmp('>=', VersionUnwrapper('0.1')) is True

    a = VersionUnwrapper('1.1a1')

    assert a.cmp('==', VersionUnwrapper('1.1')) is False
    assert a.cmp('==', VersionUnwrapper('1.1a1')) is True
    assert a.cmp('==', VersionUnwrapper('1.1.*')) is True
    assert a.cmp('==', VersionUnwrapper('0!1.1.*')) is True
    assert a.cmp('==', VersionUnwrapper('1!1.1.*')) is False

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
    assert a.cmp('==', VersionUnwrapper('0!1.1.*')) is True
    assert a.cmp('==', VersionUnwrapper('1!1.1.*')) is False

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
    assert a.cmp('===', VersionUnwrapper('0!1.1')) is False
    assert a.cmp('===', VersionUnwrapper('1!1.1')) is False

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
    assert a.cmp('>=', VersionUnwrapper('0!1.1')) is True
    assert a.cmp('>=', VersionUnwrapper('1!1.1')) is False

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
    assert a.cmp('<=', VersionUnwrapper('0!1.1')) is True
    assert a.cmp('<=', VersionUnwrapper('1!1.1')) is True
    assert a.cmp('<=', VersionUnwrapper('1!2.1')) is True

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
    assert a.cmp('>', VersionUnwrapper('0!0.1')) is True
    assert a.cmp('>', VersionUnwrapper('0!1.1')) is False
    assert a.cmp('>', VersionUnwrapper('1!0.1')) is False
    assert a.cmp('>', VersionUnwrapper('1!1.1')) is False
    assert a.cmp('>', VersionUnwrapper('1!2.1')) is False

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

    a = VersionUnwrapper('1!1.1')

    assert a.cmp('==', VersionUnwrapper('1.1')) is False
    assert a.cmp('==', VersionUnwrapper('1.1.0')) is False
    assert a.cmp('==', VersionUnwrapper('1!1.1')) is True
    assert a.cmp('==', VersionUnwrapper('1!1.1.0')) is True


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
