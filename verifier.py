from auth_db_server import AuthDBServer
from crypto_util import HashFunction
from db_adapters import MongoDB


class Verifier:

    def __init__(self, server):
        self.server = server
        self.server.destroy_db()
        self.hash_function = HashFunction()

    def verify_membership(self, value):
        proof = self.server.get_membership_proof(value)
        if proof is None:
            return False
        assert (value in proof[0][0])
        root_hash = self.build_root_hash(proof)
        return root_hash == self.server.get_root_hash()

    def get_all_values_in_proof(self, proof):
        values = []
        for node in proof:
            if node[0][0] is not None:
                values.append(node[0][0])
            if node[0][1] is not None:
                values.append(node[0][1])
        return values

    def find_adjacent_values(self, numbers, value):
        numbers.sort()
        lower = None
        upper = None
        for i in range(0, len(numbers)):
            if numbers[i] > value:
                upper = numbers[i]
                break
            lower = numbers[i]
        return lower, upper

    def verify_non_membership(self, value):
        proof = self.server.get_non_membership_proof(value)
        if proof is None:
            return False
        # Find adjacent lower and upper values
        values_in_proof = self.get_all_values_in_proof(proof)
        lower, upper = self.find_adjacent_values(values_in_proof, value)
        # Assert they are neighbours
        values_in_proof.sort()
        # TODO: Fix edge cases!
        if lower is not None and upper is not None:
            for i in range(0, len(values_in_proof)):
                x = values_in_proof[i]
                if lower == x:
                    assert values_in_proof[i+1] == upper

        # Build proof and compare to root hash
        root_hash = self.build_root_hash(proof)
        return root_hash == self.server.get_root_hash()

    def build_root_hash(self, proof):
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
        return prev_hash