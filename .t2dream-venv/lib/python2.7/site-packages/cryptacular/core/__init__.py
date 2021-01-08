# -*- coding: utf-8 -*-
#
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

__all__ = [
    'DelegatingPasswordManager',
    'PasswordChecker',
    'PasswordManager',
    'check_unicode'
]

import hmac

try:
    unicode
    def check_unicode(text):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        if not isinstance(text, str):
            raise TypeError()
        return text
except NameError:
    def check_unicode(text):
        # In Python3, PyArg_ParseTuple("ss") in the builtin crypt module
        # and our _bcrypt.c encodes unicode as utf-8, which falls short
        # of dealing with bytes but is nearly what we want.
        if not isinstance(text, str):
            raise TypeError('expected str')
        return text


class PasswordChecker(object):

    SCHEME = None
    PREFIX = None

    def check(self, encoded, password):
        """Return True if 'password' hashes to 'encoded' in this scheme.

        Most password schemes require encoded and password to be byte
        strings. The schemes included with this package convert unicode
        'encoded' and 'password' to utf-8 as necessary.
        """
        raise NotImplementedError()

    def match(self, encoded):
        """Return True if 'encoded' appears to be a valid hash for this scheme.

        Most password schemes include a recognizable prefix in their hashes."""
        return encoded.startswith(self.PREFIX)


class PasswordManager(PasswordChecker):

    def encode(self, password):
        """Return hash of 'password' using this scheme.
        """
        raise NotImplementedError()


class DelegatingPasswordManager(object):

    SCHEME = None
    PREFIX = None

    def __init__(self, fallbacks=(), **kwargs):
        self._managers = [kwargs['preferred']]
        self._managers.extend(fallbacks)

    @property
    def preferred(self):
        return self._managers[0]

    @property
    def fallbacks(self):
        return self._managers[1:]

    def encode(self, password):
        return self.preferred.encode(password)

    def check(self, encoded, password, setter=None):
        for i, manager in enumerate(self._managers):
            if manager.match(encoded):
                valid = manager.check(encoded, password)
                if valid and i > 0 and setter is not None:
                    setter(self.preferred.encode(password))
                return valid

        raise ValueError("No configured password manager for given hash.")

    def match(self, encoded):
        return True in [m.match(encoded) for m in self._managers]


def _cmp(a, b):
    a = check_unicode(a)
    b = check_unicode(b)
    return hmac.compare_digest(a, b)
