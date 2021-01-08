# -*- coding: utf-8 -*-
"""
Cryptacular password manager based on builtin ``crypt`` module (available
on Unix). Available crypt functions will vary by system. See ``man crypt``.

Usage::

    try:
        manager = CRYPTPasswordManager(cryptacular.crypt.SHA256CRYPT)
        hashed = manager.encode('secret')
        assert manager.check(hashed, 'secret') == True
    except NotImplementedError:
        print "SHA256CRYPT is not implemented on your system."
"""
# Copyright (c) 2011 Daniel Holth <dholth@fastmail.fm>
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

__all__ = ['CRYPTPasswordManager', 'OLDCRYPT', 'MD5CRYPT', 'SHA256CRYPT',
    'SHA512CRYPT', 'BCRYPT']

import os
import re
import crypt as system_crypt
import base64

from cryptacular.core import check_unicode
import cryptacular.core

OLDCRYPT = ""
BCRYPT = "$2b$"
MD5CRYPT = "$1$"
SHA256CRYPT = "$5$"
SHA512CRYPT = "$6$"


class CRYPTPasswordManager(object):
    _crypt = staticmethod(system_crypt.crypt)

    def available(self, prefix):
        # Lame 'is implemented' check.
        try:
            l = len(self._crypt('implemented?', prefix + 'xyzzy'))
        except TypeError:
            # crypt may return None if prefix is unrecognized
            return False
        if prefix == OLDCRYPT:
            if l != 13:
               return False
        elif l < 26:
            return False
        return True

    def __init__(self, prefix):
        """prefix: $1$ etc. indicating hashing scheme."""
        self.PREFIX = prefix
        if not self.available(prefix):
            raise NotImplementedError

    def encode(self, password):
        """Hash a password using the builtin crypt module."""
        salt = self.PREFIX
        salt += base64.b64encode(os.urandom(12), altchars=b'./').decode('utf-8')
        password = check_unicode(password)
        rc = self._crypt(password, salt)
        return rc

    def check(self, encoded, password):
        """Check a bcrypt password hash against a password."""
        password = check_unicode(password)
        encoded = check_unicode(encoded)
        if not self.match(encoded):
            return False
        rc = self._crypt(password, encoded)
        if rc == None:  # only if the stored password is not compatible with crypt()
            return False
        return cryptacular.core._cmp(rc, encoded)

    def match(self, hash):
        """Return True if hash starts with our prefix."""
        return hash.startswith(self.PREFIX)

