from pymongo import MongoClient
from node import Two3Node


class MongoDB():

    def __init__(self, ip='localhost', port=27017):
        self.client = MongoClient(ip, port)
        self.db = self.client.test_database
        self.nodes = self.db.nodes
        self.root_id = "root"

    def update_23_node(self, node: 'Two3Node'):
        children = {'left': node.left_child_id, 'mid': node.mid_child_id, 'right': node.right_child_id}
        values = {'left': node.left, 'right': node.right}
        update_value = {"$set": {'children': children, 'values': values, 'hash': node.hash}}
        filter = {"_id": node.node_id}
        self.nodes.update_one(filter, update_value)

    def remove_23_node(self, node: 'Two3Node'):
        filter = {"_id": node.node_id}
        self.nodes.delete_one(filter)

    def delete_left_right(self, node, delete_left):
        if delete_left:
            values = {'left': node.right, 'right': None}
        else:
            values = {'left': node.left, 'right': None}
        update_value = {"$set": {'values': values, 'hash': node.hash}}
        filter = {"_id": node.node_id}
        self.nodes.update_one(filter, update_value)
        print("here", self.nodes.find_one(filter))

    def get_23_node_by_id(self, node_id):
        if node_id is None:
            return None
        node = self.nodes.find_one({'_id': node_id})
        print(node)
        nod = Two3Node(node_id, node["values"]["left"])
        nod.right = node["values"]["right"]
        nod.left_child_id = node["children"]["left"]
        nod.mid_child_id = node["children"]["mid"]
        nod.right_child_id = node["children"]["right"]
        return nod

    def create_root(self, value, root_id):
        root = {"_id": root_id, 'children': {'left': None, 'mid': None, 'right': None},
                'values': {'left': value, 'right': None}}
        self.nodes.insert_one(root)
        return Two3Node(root["_id"], value)

    def create_23_node(self, key, children=None) -> 'Two3Node':
        if children is None:
            children = [None, None, None]
        temp_node = Two3Node("fake_id", key)
        temp_node.update(self.db)
        if len(children) == 3:
            node = {'children': {'left': children[0],
                                 'mid': children[1],
                                 'right': children[2]},
                    'values': {'left': key,
                               'right': None},
                    'hash': temp_node.hash}
        else:
            node = {'children': {'left': children[0],
                                 'mid': None,
                                 'right': children[1]},
                    'values': {'left': key,
                               'right': None},
                    'hash': temp_node.hash}
        node_id = self.nodes.insert_one(node).inserted_id
        two_3_node = Two3Node(node_id, key)
        two_3_node.left_child_id = children[0]
        two_3_node.right_child_id = children[1]

        return two_3_node

    def destroy_db(self):
        self.nodes.drop()