from pymongo import MongoClient, InsertOne, DeleteOne, UpdateOne
from node import Two3Node, HoleNode

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

    def update_many_23_nodes(self, nodes):
        operations = []
        for node in nodes:
            children = {'left': node.left_child_id, 'mid': node.mid_child_id, 'right': node.right_child_id}
            values = {'left': node.left, 'right': node.right}
            update_value = {"$set": {'children': children, 'values': values, 'hash': node.hash}}
            filter = {"_id": node.node_id}
            operations.append(UpdateOne(filter, update_value))
        if len(operations) > 0:
            self.nodes.bulk_write(operations)

    def new_root(self, node_id):
        node = self.nodes.find_one({'_id': node_id})
        root = {"_id": self.root_id, 'children': node["children"],
                'values': node["values"],
                'hash': node["hash"]}
        self.nodes.insert_one(root)

    def make_hole_node(self, node, child=None):
        children = {'left': child, 'mid': None, 'right': None}
        values = {'left': None, 'right': None}
        update_value = {"$set": {'children': children, 'values': values}}
        filter = {"_id": node.node_id}
        self.nodes.update_one(filter, update_value)
        return HoleNode(node, child)

    def remove_23_node(self, node_id):
        filter = {"_id": node_id}
        self.nodes.delete_one(filter)

    def delete_many_23_nodes(self, node_ids):
        self.nodes.delete_many({'_id': {'$in': node_ids}})

    def get_root_hash(self):
        node = self.nodes.find_one({'_id': self.root_id})
        if node is None:
            return None
        else:
            return node["hash"]

    def get_23_node_by_id(self, node_id):
        if node_id is None:
            return None
        node = self.nodes.find_one({'_id': node_id})
        nod = Two3Node(node_id, node["values"]["left"])
        nod.right = node["values"]["right"]
        nod.left_child_id = node["children"]["left"]
        nod.mid_child_id = node["children"]["mid"]
        nod.right_child_id = node["children"]["right"]
        nod.hash = node["hash"]
        return nod

    def get_many_23_nodes_by_ids(self, node_ids):
        if len(node_ids) < 1:
            return
        nodes = []
        filter = ({"_id": {"$in": node_ids}})
        nodes_in_json = self.nodes.find(filter)
        for json_node in nodes_in_json:
            node = self.convert_json_to_node(json_node)
            nodes.append(node)
        return nodes

    def create_root(self, value, root_id):
        root = {"_id": root_id, 'children': {'left': None, 'mid': None, 'right': None},
                'values': {'left': value, 'right': None}, 'hash': None}
        self.nodes.insert_one(root)
        return Two3Node(root["_id"], value)

    def convert_json_to_node(self, node):
        nod = Two3Node(node["_id"], node["values"]["left"])
        nod.right = node["values"]["right"]
        nod.left_child_id = node["children"]["left"]
        nod.mid_child_id = node["children"]["mid"]
        nod.right_child_id = node["children"]["right"]
        nod.hash = node["hash"]
        return nod

    def convert_node_to_json(self, node):
        if node.node_id is None:
            return {'children': {'left': node.left_child_id, 'mid': node.mid_child_id,
                                         'right': node.right_child_id},
                            'values': {'left': node.left, 'right': node.right}, 'hash': node.hash}
        else:
            return {"_id": node.node_id, 'children': {'left': node.left_child_id, 'mid': node.mid_child_id,
                                                              'right': node.right_child_id},
                            'values': {'left': node.left, 'right': node.right}, 'hash': node.hash}

    def create_many_23_nodes_from_node(self, nodes):
        nodes_to_insert = []
        for node in nodes:
            node_as_json = self.convert_node_to_json(node)
            nodes_to_insert.append(node_as_json)
        if len(nodes_to_insert) > 0:
            self.nodes.insert_many(nodes_to_insert)

    def create_23_node_from_node(self, node):
        node_as_json = self.convert_node_to_json(node)
        self.nodes.insert_one(node_as_json)

    def create_23_node(self, key, children=None) -> 'Two3Node':
        if children is None:
            children = [None, None, None]
        if len(children) == 3:
            node = {'children': {'left': children[0],
                                 'mid': children[1],
                                 'right': children[2]},
                    'values': {'left': key,
                               'right': None},
                    'hash': None}
        else:
            node = {'children': {'left': children[0],
                                 'mid': None,
                                 'right': children[1]},
                    'values': {'left': key,
                               'right': None},
                    'hash': None}
        node_id = self.nodes.insert_one(node).inserted_id
        two_3_node = Two3Node(node_id, key)
        two_3_node.left_child_id = children[0]
        two_3_node.right_child_id = children[1]

        return two_3_node

    def destroy_db(self):
        self.nodes.drop()
