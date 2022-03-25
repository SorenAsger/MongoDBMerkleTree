from pymongo import MongoClient
from DBInterface import Database23NodeInterface
from Node import Node, Two3Node


class MongoDB(Database23NodeInterface):

    def __init__(self, ip='localhost', port=27017):
        self.client = MongoClient(ip, port)
        self.db = self.client.test_database
        self.nodes = self.db.nodes
        self.root_id = "root"

    def update_up_from_23_node(self, node: 'Two3Node'):
        pass

    def update_23_node(self, node: 'Two3Node'):
        pass

    def remove_23_node(self, node: 'Node'):
        pass

    def get_23_node_by_id(self, node_id):
        node = self.nodes.find_one({'_id': node_id})
        # reads values and children and removes none values
        values = node["values"].values()
        children_ids = node["children"].values()
        nod = Two3Node(node_id, values[0])
        nod.right = values[1]
        nod.left_child_id = children_ids[0]
        nod.right_child_id = children_ids[2]
        nod.mid_child_id = children_ids[1]
        # should children be sorted?
        return nod

    def create_root(self, value):
        root = {"_id": "root", 'children': {'left': None, 'mid': None, 'right': None},
                'values': {'left': value, 'right': None}}
        return Two3Node(root["_id"], value)

    def create_23_node(self, key, children=None) -> 'Two3Node':
        if children is None:
            children = [None, None]
        node = {'children': {'left': children[0],
                             'mid': None,
                             'right': children[1]},
                'values': {'left': key,
                           'right': None}}
        node_id = self.nodes.insert_one(node).inserted_id
        return Two3Node(node_id, key)
