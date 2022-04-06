import hashlib


class HashFunction:
    def __init__(self):
        self.m = hashlib.sha256()

    def digest(self):
        return self.m.digest()

    def update(self, value):
        if value is not None:
            value_as_bytes = str(value).encode('utf-8')
            self.m.update(value_as_bytes)
