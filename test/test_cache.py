import unittest

from auth_db_server import AuthDBServer
from cache import Cache
from db_adapters import MongoDB
from node import Two3Node


class CacheTest(unittest.TestCase):

    def setUp(self):
        self.dbi = MongoDB()
        self.server = AuthDBServer(self.dbi)
        self.server.destroy_db()
        self.cache = Cache(self.dbi)

    def test_cached_nodes_should_be_added_to_db(self):
        node = Two3Node("id", 1)
        node2 = Two3Node("id_2", 2)

        self.cache.add(node)
        self.cache.add(node2)

        self.cache.write_cache_to_db()

        nodes_from_db = self.dbi.get_many_23_nodes_by_ids([node.node_id, node2.node_id])
        self.assertEqual(nodes_from_db[0].node_id, node.node_id)
        self.assertEqual(nodes_from_db[1].node_id, node2.node_id)
        self.assertEqual(nodes_from_db[0].left, node.left)
        self.assertEqual(nodes_from_db[1].left, node2.left)

    def test_cached_nodes_should_be_updated_in_db(self):
        node = Two3Node("id", 2)
        self.dbi.create_23_node_from_node(node)

        node.left = 100
        node.right = 200
        node.left_child_id = "left_id"
        node.right_child_id = "right_id"

        self.cache.update(node)
        self.cache.write_cache_to_db()

        node_from_db = self.dbi.get_23_node_by_id(node.node_id)

        self.assertEqual(node_from_db.node_id, node.node_id)
        self.assertEqual(node_from_db.left, 100)
        self.assertEqual(node_from_db.right, 200)
        self.assertEqual(node_from_db.left_child_id, "left_id")
        self.assertEqual(node_from_db.right_child_id, "right_id")


    def test_cached_nodes_should_be_deleted_from_db(self):
        node = Two3Node("id", 1)
        node2 = Two3Node("id_2", 2)

        self.dbi.create_23_node_from_node(node)
        self.dbi.create_23_node_from_node(node2)

        nodes_from_db = self.dbi.get_many_23_nodes_by_ids([node.node_id, node2.node_id])
        self.assertEqual(len(nodes_from_db), 2)

        self.cache.delete(node.node_id)
        self.cache.write_cache_to_db()

        nodes_from_db = self.dbi.get_many_23_nodes_by_ids([node.node_id, node2.node_id])
        self.assertEqual(len(nodes_from_db), 1)

    def test_getting_a_cached_node_should_not_come_from_db(self):
        node_in_cache = Two3Node("id", 1)
        node_not_in_cache = Two3Node("id_2", 2)

        self.dbi.create_23_node_from_node(node_in_cache)
        self.dbi.create_23_node_from_node(node_not_in_cache)

        node_in_cache.left = 123
        self.cache.add(node_in_cache)

        node_from_cache = self.cache.get(node_in_cache.node_id)
        self.assertEqual(node_from_cache.left, 123)

        node_from_db = self.cache.get(node_not_in_cache.node_id)
        self.assertEqual(node_from_db.left, 2)

    def test_updating_an_added_node_should_update_it(self):
        node = Two3Node("id", 1)

        self.cache.add(node)
        node.left = 2
        self.cache.update(node)
        self.assertEqual(self.cache.get(node.node_id).left, 2)

        node.left = 3
        self.cache.update(node)
        self.assertEqual(self.cache.get(node.node_id).left, 3)

        self.cache.write_cache_to_db()
        node_from_db = self.dbi.get_23_node_by_id(node.node_id)
        self.assertEqual(node_from_db.left, 3)