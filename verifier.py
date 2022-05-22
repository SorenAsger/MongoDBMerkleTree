import copy

from auth_db_server import AuthDBServer
from crypto_util import HashFunction, get_node_hash
from db_adapters import MongoDB


class Verifier:

    def __init__(self, server):
        self.server = server
        self.server.destroy_db()

    def verify_membership(self, value):
        proof = self.server.get_membership_proof(value)
        return self.verify_membership_proof(value, proof)

    def verify_membership_proof(self, value, proof):
        if proof is None:
            return False
        proof = copy.deepcopy(proof)
        assert (value in proof[0][0])
        root_hash = self.build_root_hash(proof, value)
        return root_hash == self.server.get_root_hash()

    def verify_non_membership_proof(self, value, proof):
        if proof is None:
            return False
        proof = copy.deepcopy(proof)
        # Check that value is not in the first node
        first_node = proof[0]
        first_node_values = first_node[0]
        assert value not in first_node_values

        # Build proof and compare to root hash
        root_hash = self.build_root_hash(proof, value)
        return root_hash == self.server.get_root_hash()

    def verify_non_membership(self, value):
        proof = self.server.get_non_membership_proof(value)
        return self.verify_non_membership_proof(value, proof)


    def check_value_comes_from_correct_child(self, value, left, right, child_is_coming_from):
        # Coming from left child
        if child_is_coming_from == 0:
            assert value < left
        # Coming from mid child
        if child_is_coming_from == 1:
            assert left < value < right
        # Coming from right child
        if child_is_coming_from == 2:
            if right is None:
                left < value
            else:
                right < value

    def build_root_hash(self, proof, value):
        prev_hash = None
        first_node = True
        for node in proof:
            left = node[0][0]
            right = node[0][1]
            if right is not None:
                assert (left < right)

            # Set the previously calculated hash to the hash
            # of calling child of node's hash
            child_is_coming_from = None
            for i in range(1, 4):
                if node[i] == 'c':
                    node[i] = prev_hash
                    child_is_coming_from = i - 1
            if not first_node:
                assert child_is_coming_from is not None
                self.check_value_comes_from_correct_child(value, left, right, child_is_coming_from)

            left_child_hash = node[1]
            mid_child_hash = node[2]
            right_child_hash = node[3]
            values = [left, right]
            hashes = [left_child_hash, mid_child_hash, right_child_hash]

            prev_hash = get_node_hash(values, hashes)
            first_node = False
        return prev_hash

