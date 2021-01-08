from __future__ import unicode_literals
from nose.tools import eq_, raises, assert_false, assert_true, assert_not_equal
from cryptacular.crypt import *

class TestCRYPTPasswordManager(object):
    snowpass = "hashy the \N{SNOWMAN}"

    PREFIX = OLDCRYPT

    def setup(self):
        self.manager = CRYPTPasswordManager(self.PREFIX)

    @raises(TypeError)
    def test_None1(self):
        self.manager.encode(None)

    @raises(TypeError)
    def test_None2(self):
        self.manager.check(None, 'xyzzy')

    @raises(TypeError)
    def test_None3(self):
        hash = self.manager.encode('xyzzy')
        self.manager.check(hash, None)

    def test_badhash(self):
        eq_(self.manager.check('$p5k2$400$ZxK4ZBJCfQg=$kBpklVI9kA13kP32HMZL0rloQ1M=', self.snowpass), False)

    def test_shorthash(self):
        manager = self.manager
        def match(hash):
            return True
        manager.match = match
        short_hash = manager.encode(self.snowpass)[:11]
        assert_true(manager.match(short_hash))
        assert_false(manager.check(short_hash, self.snowpass))

    def test_emptypass(self):
        self.manager.encode('')

    def test_general(self):
        manager = self.manager
        hash = manager.encode(self.snowpass)
        eq_(manager.match(hash), True)
        assert hash.startswith(self.PREFIX)
        assert_true(manager.check(hash, self.snowpass))
        password = "xyzzy"
        hash = manager.encode(password)
        assert_true(manager.check(hash, password))
        assert_false(manager.check(password, password))
        assert_not_equal(manager.encode(password), manager.encode(password))

available = CRYPTPasswordManager('').available

if available(BCRYPT):
    class TestCPM_BCRYPT(TestCRYPTPasswordManager):
        PREFIX = BCRYPT

if available(MD5CRYPT):
    class TestCPM_MD5CRYPT(TestCRYPTPasswordManager):
        PREFIX = MD5CRYPT

if available(SHA256CRYPT):
    class TestCPM_SHA256CRYPT(TestCRYPTPasswordManager):
        PREFIX = SHA256CRYPT

if available(SHA512CRYPT):
    class TestCPM_SHA512CRYPT(TestCRYPTPasswordManager):
        PREFIX = SHA512CRYPT

@raises(NotImplementedError)
def test_bogocrypt():
    CRYPTPasswordManager('$bogo$')

@raises(NotImplementedError)
def test_oddcrypt():
    """crypt.crypt with empty prefix returns hash != 13 characters?"""
    class BCPM(CRYPTPasswordManager):
        _crypt = lambda x, y, z: '4' * 14
    BCPM('')
