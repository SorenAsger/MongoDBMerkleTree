import hashlib


class HashFunction:
    def __init__(self):
        self.m = hashlib.sha256()

    def digest(self):
        return self.m.digest()

    def update(self, value):
        if type(value) == str:
            value = value.encode('utf-8')
            self.m.update(value)
        elif type(value) == int:
            self.m.update(value.to_bytes(2, byteorder='big'))