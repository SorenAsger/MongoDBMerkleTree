from auth_db_server import AuthDBServer
from crypto_util import HashFunction
from db_adapters import MongoDB


class Verifier:

    def __init__(self):
        self.server = AuthDBServer(MongoDB())
        self.server.destroy_db()
        self.hash_function = HashFunction()

    def verify_membership(self, value):
        proof = self.server.get_membership_proof(value)
        if proof is None:
            return False
        assert (value in proof[0][0])

        prev_hash = None
        for node in proof:
            self.hash_function.update(node[0][0])  # left value
            self.hash_function.update(node[0][1])  # right value
            # Set the previously calculated hash to the hash
            # of calling child of node's hash
            for i in range(1, 4):
                if node[i] == 'caller':
                    node[i] = prev_hash

            self.hash_function.update(node[1])  # Left child hash
            self.hash_function.update(node[2])  # mid child hash
            self.hash_function.update(node[3])  # right child hash
            prev_hash = self.hash_function.digest()

        return prev_hash == self.server.get_root_hash()
