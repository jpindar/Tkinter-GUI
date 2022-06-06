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
# TODO  unit tests

import struct
from typing import Union
from base64 import urlsafe_b64encode, urlsafe_b64decode
from Crypto.Cipher import AES


def pad16(s: Union[str, bytes]) -> bytes:
    if isinstance(s, str):
        s = s.encode()
    r: bytes = struct.pack('>I', len(s))  # save the length
    r = r + s                      # append it
    pad: str = '\x00' * ((16 - len(r) % 16) % 16)  # pad with zeros
    r = r + pad.encode()
    return r  # and r is now a multiple of 16 chars long


def unpad16(s: bytes) -> bytes:
    n = struct.unpack('>I', s[:4])[0]
    r: bytes = s[4:n + 4]
    return r


class Crypt(object):
    def __init__(self, password: str):
        self.cipher = AES.new(pad16(password), AES.MODE_ECB)

    def encrypt(self, s: str) -> bytes:
        b: bytes = pad16(s)
        return self.cipher.encrypt(b)

    def decrypt(self, s) -> bytes:
        t: bytes = self.cipher.decrypt(s)
        r: bytes = unpad16(t)
        return r


def encrypt(s: str, p: str) -> str:
    c = Crypt(p)
    b: bytes = c.encrypt(s)
    r: str = urlsafe_b64encode(b).decode()
    return r


def decrypt(s: str, p: str) -> str:
    c = Crypt(p)
    s2: bytes = urlsafe_b64decode(s)
    r: str = c.decrypt(s2).decode()
    return r


if __name__ == '__main__':
    p: str = 'password'
    t: str = 'my message'
    x: str = encrypt(t, p)
    y: str = decrypt(x, p)
    print([x, y])



