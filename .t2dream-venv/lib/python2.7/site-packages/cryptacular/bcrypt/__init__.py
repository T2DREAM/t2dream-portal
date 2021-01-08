# Copyright (c) 2009 Daniel Holth <dholth@fastmail.fm>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

__all__ = ['BCRYPTPasswordManager']


import os
import re

from cryptacular.bcrypt._bcrypt import crypt_rn, crypt_gensalt_rn
from cryptacular.core import _cmp, check_unicode


class BCRYPTPasswordManager(object):
    # for testing
    crypt_rn = crypt_rn
    crypt_gensalt_rn = crypt_gensalt_rn

    SCHEME = 'BCRYPT'
    PREFIX = '$2a$'
    _rounds = 10

    _bcrypt_syntax = re.compile('\$2a\$[0-9]{2}\$[./A-Za-z0-9]{53}')

    def encode(self, text, rounds=None):
        '''Hash a password using bcrypt.

        Note: only the first 72 characters of password are significant.
        '''
        rounds = rounds or self._rounds
        settings = self.crypt_gensalt_rn(self.PREFIX, rounds, os.urandom(16))
        if settings is None:
            raise ValueError('_bcrypt.crypt_gensalt_rn returned None')

        encoded = self.crypt_rn(check_unicode(text), settings)
        if encoded is None:
            raise ValueError('_bcrypt.crypt_rn returned None')

        return encoded

    def check(self, encoded, text):
        '''Check a bcrypt password hash against a password.
        '''
        if not self.match(encoded):
            return False

        encoded_text = self.crypt_rn(check_unicode(text), encoded)
        if encoded_text is None:
            raise ValueError('_bcrypt.crypt_rn returned None')

        return _cmp(encoded_text, check_unicode(encoded))

    def match(self, hash):
        '''Return True if hash looks like a BCRYPT password hash.
        '''
        return self._bcrypt_syntax.match(hash) is not None

