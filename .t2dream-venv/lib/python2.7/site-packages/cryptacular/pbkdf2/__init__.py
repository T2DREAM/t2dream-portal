# Copyright (c) 2009 Daniel Holth <dholth@fastmail.fm>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import absolute_import

__all__ = ['PBKDF2PasswordManager']

import os
from base64 import urlsafe_b64encode, urlsafe_b64decode
from cryptacular.core import check_unicode
import cryptacular.core
try: # pragma NO COVERAGE
    import M2Crypto.EVP
    _pbkdf2 = M2Crypto.EVP.pbkdf2
except (ImportError, AttributeError): # pragma NO COVERAGE
    from pbkdf2 import PBKDF2
    def _pbkdf2(password, salt, rounds, keylen):
        return PBKDF2(password, salt, rounds).read(keylen)

class PBKDF2PasswordManager(object):

    SCHEME = "PBKDF2"
    PREFIX = "$p5k2$"
    ROUNDS = 1<<12

    def encode(self, password, salt=None, rounds=None, keylen=20):
        if salt is None:
            salt = os.urandom(16)
        rounds = rounds or self.ROUNDS
        password = check_unicode(password)
        key = _pbkdf2(password, salt, rounds, keylen)
        hash =  self.PREFIX.encode('iso8859-1') + \
                ('%x' % rounds).encode('iso8859-1') + b'$' + \
                urlsafe_b64encode(salt) + b'$' + \
                urlsafe_b64encode(key)
        return hash.decode('utf-8')

    def check(self, encoded, password):
        encoded = check_unicode(encoded)
        if not self.match(encoded):
            return False
        iter, salt, key = encoded[len(self.PREFIX):].split('$')
        iter = int(iter, 16)
        salt = urlsafe_b64decode(salt.encode('utf-8'))
        keylen = len(urlsafe_b64decode(key.encode('utf-8')))
        hash = self.encode(password, salt, iter, keylen)
        return cryptacular.core._cmp(hash, encoded)

    def match(self, encoded):
        """True if encoded appears to match this scheme."""
        encoded = check_unicode(encoded)
        return encoded.startswith(self.PREFIX)
 
