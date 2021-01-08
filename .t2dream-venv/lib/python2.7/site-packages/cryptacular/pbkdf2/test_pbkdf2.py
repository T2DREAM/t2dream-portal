# Tests for the pbkdf2 module.
# Copyright 2004 Matt Johnston <matt @ ucc asn au>
# Copyright 2009 Daniel Holth <dholth@fastmail.fm>
# This code may be freely used and modified for any purpose.
from __future__ import unicode_literals
from nose.tools import eq_, raises, assert_not_equal
from cryptacular.pbkdf2 import PBKDF2PasswordManager
from binascii import hexlify, unhexlify

import cryptacular.pbkdf2
pbkdf2 = cryptacular.pbkdf2._pbkdf2

def test():
    # test vector from rfc3211
    salt = unhexlify( b'1234567878563412' )
    password = b'All n-entities must communicate with other n-entities via n-1 entiteeheehees'
    itercount = 500
    keylen = 16
    ret = pbkdf2( password, salt, itercount, keylen )
    eq_(hexlify(ret), b"6A8970BF68C92CAEA84A8DF285108586".lower())

    # from botan
    password = unhexlify(b'6561696D72627A70636F706275736171746B6D77')
    expect = b'C9A0B2622F13916036E29E7462E206E8BA5B50CE9212752EB8EA2A4AA7B40A4CC1BF'
    salt = unhexlify(b'45248F9D0CEBCB86A18243E76C972A1F3B36772A')
    keylen = 34
    itercount = 100
    ret = pbkdf2( password, salt, itercount, keylen )
    hexret = hexlify(ret).upper()
    eq_(hexret, expect)

def test_passwordmanager():
    from base64 import urlsafe_b64decode
    manager = PBKDF2PasswordManager()
    # Never call .encode with a salt.
    salt = urlsafe_b64decode(b'ZxK4ZBJCfQg=')
    text = "hashy the \N{SNOWMAN}"
    hash = manager.encode(text, salt)
    eq_(hash, '$p5k2$1000$ZxK4ZBJCfQg=$jJZVscWtO--p1-xIZl6jhO2LKR0=')
    password = "xyzzy"
    hash = manager.encode(password)
    assert manager.check(hash, password)
    assert not manager.check(password, password)
    assert_not_equal(manager.encode(password), manager.encode(password))
    hash = manager.encode(text, salt, rounds=1)
    eq_(hash, "$p5k2$1$ZxK4ZBJCfQg=$Kexp0NAVgxlDwoA-TS34o8o2Okg=")
    assert manager.check(hash, text)

if __name__ == "__main__":
    test() # pragma: NO COVERAGE
