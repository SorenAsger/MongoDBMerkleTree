import hashlib
import struct


class HashFunction:
    def __init__(self):
        self.m = hashlib.sha256()

    def digest(self):
        return self.m.digest()

    def update(self, value):
        encoded_val = str(value).encode('utf-8')
        self.m.update(encoded_val)
