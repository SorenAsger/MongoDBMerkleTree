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
        children = {'left': node.left_child_id, 'mid': node.mid_child_id, 'right': node.right_child_id}
        values = {'left': node.left, 'right': node.right}
        update_value = {"$set": {'children': children, 'values': values}}
        filter = {"_id": node.node_id}
        self.nodes.update_one(filter, update_value)

    def remove_23_node(self, node: 'Two3Node'):
        filter = {"_id": node.node_id}
        self.nodes.delete_one(filter)

    def get_23_node_by_id(self, node_id):
        if node_id is None:
            return None
        node = self.nodes.find_one({'_id': node_id})
        nod = Two3Node(node_id, node["values"]["left"])
        nod.right = node["values"]["right"]
        nod.left_child_id = node["children"]["left"]
        nod.right_child_id = node["children"]["mid"]
        nod.mid_child_id = node["children"]["right"]
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
        two_3_node = Two3Node(node_id, key)
        two_3_node.left_child_id = children[0]
        two_3_node.right_child_id = children[1]
        return two_3_node

    def destroy_db(self):
        self.nodes.drop()
