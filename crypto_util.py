import hashlib


class HashFunction:
    def __init__(self):
        self.m = hashlib.sha256()

    # Digest both returns the hash of the
    # bytes so far and creates a new instance
    # of the hash object.
    def digest(self):
        result = self.m.digest()
        self.m = hashlib.sha256()
        return result


    def update(self, value):
        if value is not None:
            value_as_bytes = str(value).encode('utf-8')
            self.m.update(value_as_bytes)
