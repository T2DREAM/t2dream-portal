# -*- coding: utf-8 -*-
import sys
from nose.tools import *
from cryptacular.core import *

if sys.hexversion < 0x3000000:
    def test_doctest():
        """
        >>> import cryptacular.core
        >>> import cryptacular.bcrypt
        >>> import cryptacular.pbkdf2
        >>> bcrypt = cryptacular.bcrypt.BCRYPTPasswordManager()
        >>> pbkdf2 = cryptacular.pbkdf2.PBKDF2PasswordManager()
        >>> delegator = cryptacular.core.DelegatingPasswordManager(preferred=bcrypt, fallbacks=(pbkdf2,))
        >>> users = {'one':{'password':'xyzzy'}, 'two':{'password':u'hashy the \N{SNOWMAN}'}}
        >>> for key in users: users[key]['hash'] = pbkdf2.encode(users[key]['password'])
        >>> bcrypt.match(users['one']['password'])
        False
        >>> def set_hash(hash): users['one']['hash'] = hash
        >>> delegator.check(users['one']['hash'], users['one']['password'], setter=set_hash)
        True
        >>> bcrypt.match(users['one']['hash'])
        True
        >>> def set_hash(hash): raise Exception("Should not re-set a preferred hash")
        >>> delegator.check(users['one']['hash'], users['one']['password'], setter=set_hash)
        True
        >>> bcrypt.match(users['two']['hash'])
        False
        >>> pbkdf2.match(users['two']['hash'])
        True
        >>> delegator.check(users['two']['hash'], users['two']['password'])
        True
        >>> bcrypt.match(users['two']['hash'])
        False
        >>> pbkdf2.match(users['two']['hash'])
        True
        >>> [delegator.match(users[key]['hash']) for key in users]
        [True, True]
        >>> delegator.match('*69')
        False
        >>> bcrypt.match(delegator.encode('xyzzy'))
        True
        >>> delegator.preferred is bcrypt
        True
        >>> delegator.fallbacks == [pbkdf2]
        True
        """

@raises(ValueError)
def test_bad_check():
    import cryptacular.core
    import cryptacular.bcrypt
    import cryptacular.pbkdf2
    bcrypt = cryptacular.bcrypt.BCRYPTPasswordManager()
    pbkdf2 = cryptacular.pbkdf2.PBKDF2PasswordManager()
    delegator = cryptacular.core.DelegatingPasswordManager(preferred=bcrypt, fallbacks=(pbkdf2,))
    delegator.check('{notahash}#', 'wurble')

def test_interfaces():
    checker = PasswordChecker()
    @raises(NotImplementedError)
    def check():
        checker.check('foo', 'foo')
    check()
    checker.PREFIX = '{foo}'
    assert_true(checker.match('{foo}bar'))
    eq_(PasswordChecker().SCHEME, None)
    eq_(PasswordChecker().PREFIX, None)

    manager = PasswordManager()
    @raises(NotImplementedError)
    def encode():
        manager.encode('foo')
    encode()

