import random
import unittest

from auth_db_server import AuthDBServer
from db_adapters import MongoDB
from verifier import Verifier


class VerifierTest(unittest.TestCase):

    def setUp(self):
        self.server = AuthDBServer(MongoDB())
        self.server.destroy_db()
        self.verifier = Verifier(self.server)

    def test_values_in_db_should_be_verified(self):
        self.insert_sorted(100)
        self.server.print_db()
        for i in range(1, 2):
            membership = self.verifier.verify_membership(i)
            self.assertTrue(membership)

    def test_values_not_in_db_should_not_be_verified(self):
        self.insert_sorted(100)
        for i in range(100, 200):
            self.assertTrue(self.verifier.verify_non_membership(i))

    def test_correct_adjacent_values_should_be_found(self):
        numbers = list(range(0, 10, 2))
        value = 5
        lower, upper = self.verifier.find_adjacent_values(numbers, value)
        self.assertEqual(lower, 4)
        self.assertEqual(upper, 6)

    def test_all_values_in_proof_should_be_found(self):
        self.insert_sorted(7)
        proof = self.server.get_membership_proof(1)
        numbers = self.verifier.get_all_values_in_proof(proof)
        numbers.sort()
        self.assertEqual(numbers[0], 1)
        self.assertEqual(numbers[1], 3)
        self.assertEqual(len(numbers), 2)

    def insert_many(self, n):
        for i in range(0, n):
            self.server.insert(random.randint(0, n))

    def insert_sorted(self, n):
        for i in range(0, n):
            self.server.insert(i)

