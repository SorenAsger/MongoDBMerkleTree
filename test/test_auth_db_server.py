import random
import unittest

from db_adapters import MongoDB
from auth_db_server import AuthDBServer


class AuthDBServerTest(unittest.TestCase):

    def setUp(self):
        self.server = AuthDBServer(MongoDB())
        self.server.destroy_db()

    def test_all_nodes_have_hash_with_sorted_insertions(self):
        for i in range(0, 100):
            self.server.insert(i)

        cursor = self.server.get_db_cursor()
        for node in cursor:
            self.assertTrue(node['hash'] is not None)

    def test_all_nodes_have_hash_with_random_insertions(self):
        numbers = [i for i in range(0, 100)]
        random.shuffle(numbers)
        for x in numbers:
            self.server.insert(x)

        cursor = self.server.get_db_cursor()
        for node in cursor:
            self.assertTrue(node['hash'] is not None)

    def test_inserting_floats_should_work(self):
        for i in range(1, 20):
            self.server.insert(1/i)

        for i in range(1, 20):
            self.assertTrue(self.server.contains(1/i))

    def test_inserting_negative_numbers_should_work(self):
        for i in range(-10, 0):
            self.server.insert(i)

        for i in range(-10, 0):
            self.assertTrue(self.server.contains(i))

    def test_inserting_strings_should_work(self):
        for i in range(10, 200):
            self.server.insert(chr(i))

        for i in range(10, 200):
            self.assertTrue(self.server.contains(chr(i)))

    def test_40_sorted_insertions_should_give_38_nodes(self):
        for i in range(0, 40):
            self.server.insert(i)

        n = 0
        cursor = self.server.get_db_cursor()
        for node in cursor:
            n += 1

        self.assertEqual(n, 38)

    def test_root_hash_should_change_after_each_insertion(self):
        numbers = [i for i in range(0, 100)]
        random.shuffle(numbers)

        prev_root_hash = None
        for n in numbers:
            self.server.insert(n)
            self.assertNotEqual(prev_root_hash, self.server.get_root_hash())
            prev_root_hash = self.server.get_root_hash()

    def test_deleting_an_element_should_remove_it_from_tree(self):
        numbers = [i for i in range(0, 100)]
        random.shuffle(numbers)

        for i in numbers:
            self.server.insert(i)

        random.shuffle(numbers)
        numbers_in_tree = numbers[:50]
        numbers_deleted = numbers[50:]

        for v in numbers_deleted:
            self.server.delete(v)

        for n in numbers_deleted:
            self.assertFalse(self.server.contains(n))

        for n in numbers_in_tree:
            self.assertTrue(self.server.contains(n))

    def test_root_hash_changes_after_insertion(self):
        numbers = [i for i in range(0, 100)]
        random.shuffle(numbers)

        for x in numbers:
            bef_hash = self.server.get_root_hash()
            self.server.insert(x)
            aft_hash = self.server.get_root_hash()
            self.assertFalse(bef_hash == aft_hash)

    def test_root_hash_changes_after_deletion(self):
        numbers = [i for i in range(0, 100)]
        random.shuffle(numbers)

        for x in numbers:
            self.server.insert(x)

        random.shuffle(numbers)

        for i in range(0,50):
            bef_hash = self.server.get_root_hash()
            val = numbers[i]
            self.server.delete(val)
            aft_hash = self.server.get_root_hash()
            self.assertFalse(bef_hash == aft_hash)


if __name__ == '__main__':
    unittest.main()