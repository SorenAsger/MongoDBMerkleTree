import unittest

from auth_db_server import AuthDBServer
from cache import Cache
from db_adapters import MongoDB


class CacheTest(unittest.TestCase):

    def setUp(self):
        self.dbi = MongoDB()
        self.server = AuthDBServer(self.dbi)
        self.server.destroy_db()
        self.cache = Cache(self.dbi)

    def test_cached_nodes_should_be_added_to_db(self):
        pass