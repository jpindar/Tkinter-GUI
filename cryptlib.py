"""
Project: device_GUI
File: cryptlib.py
Date: 3/29/2019
https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password
http://www.pycrypto.org/   aka   https://www.dlitz.net/software/pycrypto/
https://pypi.org/project/pycrypto/
https://paste.ubuntu.com/11024555/
PyCrypto is public domain
"""

import struct
from base64 import urlsafe_b64encode, urlsafe_b64decode
from Crypto.Cipher import AES


def pad16(s):
    if isinstance(s, str):
        s = s.encode()
    n = struct.pack('>I', len(s))  # save the length
    r = n + s                      # append it
    pad = '\x00' * ((16 - len(r) % 16) % 16)  # pad with zeros
    r = r + pad.encode()
    return r  # and r is now a multiple of 16 chars long


def unpad16(s):
    n = struct.unpack('>I', s[:4])[0]
    return s[4:n + 4]  # and r is now it's original length


class Crypt(object):
    def __init__(self, password):
        password = pad16(password)
        self.cipher = AES.new(password, AES.MODE_ECB)

    def encrypt(self, s):
        s = pad16(s)
        return self.cipher.encrypt(s)

    def decrypt(self, s):
        t = self.cipher.decrypt(s)
        return unpad16(t)


def encrypt(s, p):
    c = Crypt(p)
    b = c.encrypt(s)
    r = urlsafe_b64encode(b).decode()
    return r


def decrypt(s, p):
    c = Crypt(p)
    s2 = urlsafe_b64decode(s)
    r = c.decrypt(s2).decode()
    return r


if __name__ == '__main__':
    p = 'password'
    t = 'my message'
    x = encrypt(t, p)
    y = decrypt(x, p)
    print([x, y])



