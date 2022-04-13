import random
import unittest

from auth_db_server import AuthDBServer
from db_adapters import MongoDB
from verifier import Verifier


class VerifierTest(unittest.TestCase):

    def setUp(self):
        self.server = AuthDBServer(MongoDB())
        self.server.destroy_db()
        self.verifier = Verifier()

    def test_values_in_db_should_be_verified(self):
        self.insert_sorted(100)
        for i in range(0, 100):
            self.assertTrue(self.verifier.verify_membership(i))

    def test_values_not_in_db_should_not_be_verified(self):
        self.insert_sorted(100)
        for i in range(100, 200):
            self.assertFalse(self.verifier.verify_membership(i))

    def insert_many(self, n):
        for i in range(0, n):
            self.server.insert(random.randint(0, n))

    def insert_sorted(self, n):
        for i in range(0, n):
            self.server.insert(i)
