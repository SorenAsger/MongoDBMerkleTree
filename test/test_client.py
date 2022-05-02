import unittest
import random

from auth_db_server import AuthDBServer
from db_adapters import MongoDB
from client import Client
from cache import Cache


class ClientTest(unittest.TestCase):

    def setUp(self):
        dbi = MongoDB()
        cache = Cache(dbi, write_to_db=True)
        self.server = AuthDBServer(dbi, cache)
        self.server.destroy_db()
        self.client = Client(self.server)

    def test_client_inserts_is_the_same_as_server(self):
        n = 100
        self.insert_many(n, True)

    def test_client_deletes_is_the_same_as_server(self):
        n = 100
        self.insert_many(n, False)
        numbers = [i for i in range(n)]
        random.shuffle(numbers)
        for i in range(n):
            if i % 100 == 0:
                print(i)
            self.assertTrue(self.client.delete(numbers[i]))

    def insert_many(self, n, assert_on):
        numbers = [i for i in range(n)]
        random.shuffle(numbers)
        for i in range(0, n):
            if assert_on:
                self.assertTrue(self.client.insert(numbers[i]))
            else:
                self.server.insert(numbers[i])

    def insert_sorted(self, n):
        for i in range(0, n):
            self.server.insert(i)