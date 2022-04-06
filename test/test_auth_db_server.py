import random
import unittest

from db_adapters import MongoDB
from auth_db_server import AuthDBServer


class AuthDBServerTest(unittest.TestCase):

    def setUp(self):
        self.server = AuthDBServer(MongoDB())

    def test_all_nodes_have_hash_with_sorted_insertions(self):
        self.server.destroy_db()

        for i in range(0, 100):
            self.server.insert(i)

        cursor = self.server.get_db_cursor()
        for node in cursor:
            self.assertTrue(node['hash'] is not None)

    def test_all_nodes_have_hash_with_random_insertions(self):
        n = 40
        self.server.destroy_db()

        for i in range(0, n):
            self.server.insert(random.randint(0, n))

        cursor = self.server.get_db_cursor()
        for node in cursor:
            self.assertTrue(node['hash'] is not None)

    def test_40_sorted_insertions_should_give_38_nodes(self):
        self.server.destroy_db()

        for i in range(0, 40):
            self.server.insert(i)

        n = 0
        cursor = self.server.get_db_cursor()
        for node in cursor:
            n += 1

        self.assertEqual(n, 38)

if __name__ == '__main__':
    unittest.main()