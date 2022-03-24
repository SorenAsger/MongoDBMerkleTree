import random

from pymongo import MongoClient
import cProfile

client = MongoClient('localhost', 27017)
db = client.test_database
nodes = db.nodes
root_id = "root"


class DatabaseInterface:

    def get_node_by_id(self, node_id):
        raise NotImplementedError()

    def insert_node(self, node: 'Node'):
        raise NotImplementedError()

    def remove_node(self, node: 'Node'):
        raise NotImplementedError()


class MongoDB(DatabaseInterface):

    def __init__(self, ip='localhost', port=27017):
        self.client = MongoClient(ip, port)
        self.db = client.test_database
        self.nodes = self.db.nodes
        self.root_id = "root"

    def get_node_by_id(self, node_id):
        node = self.nodes.find_one({'_id': node_id})
        # reads values and children and removes none values
        values = [v for v in node["values"].values() if v]
        children_ids = [v for v in node["children"].values() if v]
        # should children be sorted?
        return Node(node_id, sorted(values), children_ids)

    def insert_node(self, node: 'Node'):
        def create_mongodb_node():
            pass

        self.nodes.insert_one(create_mongodb_node())

    def remove_node(self, node: 'Node'):
        pass

    def update_node(self, node: 'Node'):
        pass

    def get_23node_by_id(self, node_id):
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


dbi = MongoDB()


class Node:

    def __init__(self, node_id, values, children_ids):
        self.node_id = node_id
        self.values = values
        self.children_ids = children_ids

    def get_values(self):
        return self.values

    def get_children_ids(self):
        return self.children_ids

    def is_2_node(self):
        return len(self.values) == 1


class Two3Node:

    def __init__(self, node_id, left):
        self.left = left
        self.node_id = node_id
        self.right = None
        self.left_child_id = None
        self.right_child_id = None
        self.mid_child_id = None

    def is_2_node(self):
        return self.right is None

    def __eq__(self, other: 'Two3Node'):
        return self.node_id == other.node_id


def find_nearest_node_and_parent(value):
    current = get_node_by_id(root_id)
    parent = None
    nearest_node = None
    depth = 0
    while current is not None:
        depth += 1
        values = current["values"]
        children = current["children"]
        # If the value is in the current node
        if (value is values["left"] or value is values["right"]):
            return current, nearest_node
        # 2-node
        if values["right"] is None:
            if value < values["left"]:
                path = "left"
            else:
                path = "right"
        # 3-node
        else:
            if value < values["left"]:
                path = "left"
            elif value > values["right"]:
                path = "right"
            else:
                path = "mid"
        parent = nearest_node
        nearest_node = current
        current = get_node_by_id(children[path])
    print("depth of lookup: " + str(depth) + " for value: " + str(value))
    return nearest_node, parent


def node_contains_value(value, node):
    values = node["values"]
    return values["left"] == value or values["right"] == value


def contains(value):
    nearest_node, _ = find_nearest_node_and_parent(value)
    return node_contains_value(value, nearest_node)


def is_2_node(node):
    return node["values"]["right"] is None


def is_3_node(node):
    return node["values"]["right"] is not None


def insert(value):
    insert_location, parent = find_nearest_node_and_parent(value)
    if insert_location is not None and node_contains_value(value, insert_location):
        print("value " + str(value) + " is already in the tree.")
    elif insert_location is None:
        insert_empty_tree(value)
    elif is_2_node(insert_location):
        insert_2_node(value, insert_location)
    elif parent is None:
        insert_3_node_root(value, insert_location)
    elif is_2_node(parent):
        insert_3_node_2_parent(value, insert_location, parent)
    else:
        insert_3_node_3_parent(value, insert_location, parent)


def insert_3_node_root(value, insert_location):
    values = [insert_location["values"]["left"], insert_location["values"]["right"], value]
    values.sort()
    min = values[0]
    mid = values[1]
    max = values[2]

    # Create 2 new nodes for min and max
    min_node = {'children': {'left': None, 'mid': None, 'right': None}, 'values': {'left': min, 'right': None}}
    max_node = {'children': {'left': None, 'mid': None, 'right': None}, 'values': {'left': max, 'right': None}}
    min_node_id = nodes.insert_one(min_node).inserted_id
    max_node_id = nodes.insert_one(max_node).inserted_id

    insert_location["children"]["left"] = min_node_id
    insert_location["children"]["right"] = max_node_id
    insert_location["values"]["left"] = mid
    insert_location["values"]["right"] = None

    update_value = {"$set": {'children': insert_location["children"], 'values': insert_location["values"]}}
    filter = {"_id": insert_location["_id"]}
    nodes.update_one(filter, update_value)


def insert_empty_tree(value):
    root = {"_id": "root", 'children': {'left': None, 'mid': None, 'right': None},
            'values': {'left': value, 'right': None}}
    nodes.insert_one(root)


def split_node(node, value, left_children=None, right_children=None):
    values = [node.left, node.right, value]
    values.sort()
    min_node = dbi.create_23_node(values[0], left_children)
    max_node = dbi.create_23_node(values[2], right_children)
    return min_node, max_node, values[1]


def insert_3_node_3_parent(value, insert_location: 'Two3Node', parent: 'Two3Node'):
    min_node, max_node, mid = split_node(insert_location, value)

    # Now we need to reconstruct pointers from parent min and parent max to the children
    left_child = dbi.get_23node_by_id(parent.left_child_id)
    mid_child = dbi.get_23node_by_id(parent.mid_child_id)
    right_child = dbi.get_23node_by_id(parent.right_child_id)

    all_children = [left_child, mid_child, right_child, min_node, max_node]
    # all_children contains the previous children (left, mid, right) and the new nodes (min and max)
    # We now remove the node that was split and replaced with min and max
    all_children = [child for child in all_children if child != insert_location]
    all_children.sort(key=lambda x: x.left)

    parent_min, parent_max, mid = split_node(parent, mid, left_children=all_children[:2],
                                             right_children=all_children[2:])
    parent.left_child_id = parent_min
    parent.right_child_id = parent_max
    parent.mid_child_id = None
    # TODO: Update parent in database and delete insert_location from database
    # TODO: Could maybe be more efficient to not delete insert_location and reuse it instead?
    """
    # Create 2 new nodes for top min and top max
    # if inserted in left subtree
    inserted_in_left_subtree = None
    if inserted_in_left_subtree:
        left_subtree = {
            'children': {'left': parent["children"]["left"], 'mid': None, 'right': parent["children"]["mid"]},
            'values': {'left': parent_min, 'right': None}}
        right_subtree = {'children': {'left': min_node_id, 'mid': None, 'right': max_node_id},
                         'values': {'left': parent_max, 'right': None}}
        top_min_node_id = nodes.insert_one(left_subtree).inserted_id
        top_max_node_id = nodes.insert_one(right_subtree).inserted_id
    else:  # no clue if this works
        left_subtree = {'children': {'left': min_node_id, 'mid': None, 'right': max_node_id},
                        'values': {'left': parent_min, 'right': None}}
        right_subtree = {
            'children': {'left': parent["children"]["mid"], 'mid': None, 'right': parent["children"]["right"]},
            'values': {'left': parent_max, 'right': None}}
        top_min_node_id = nodes.insert_one(left_subtree).inserted_id
        top_max_node_id = nodes.insert_one(right_subtree).inserted_id

    # Put middle value in parent and update parent to point to the 2 new children
    parent["children"]["left"] = top_min_node_id
    parent["children"]["mid"] = None
    parent["children"]["right"] = top_max_node_id
    parent["values"]["left"] = parent_mid
    parent["values"]["right"] = None
    update_value = {"$set": {'children': parent["children"], 'values': parent["values"]}}
    filter = {"_id": parent["_id"]}
    nodes.update_one(filter, update_value)

    # Delete old node
    nodes.delete_one({"_id": insert_location["_id"]})
    """


def insert_3_node_2_parent(value, insert_location, parent):
    values = [insert_location["values"]["left"], insert_location["values"]["right"], value]
    values.sort()
    min = values[0]
    mid = values[1]
    max = values[2]

    # Create 2 new nodes for min and max
    min_node = {'children': {'left': None, 'mid': None, 'right': None}, 'values': {'left': min, 'right': None}}
    max_node = {'children': {'left': None, 'mid': None, 'right': None}, 'values': {'left': max, 'right': None}}
    min_node_id = nodes.insert_one(min_node).inserted_id
    max_node_id = nodes.insert_one(max_node).inserted_id

    # Put middle value in parent and update it to point to the 2 new children
    if value > parent["values"]["left"]:
        parent["children"]["mid"] = min_node_id
        parent["children"]["right"] = max_node_id
        parent["values"]["right"] = mid
    else:
        parent["children"]["left"] = min_node_id
        parent["children"]["mid"] = max_node_id
        parent["values"]["right"] = parent["values"]["left"]
        parent["values"]["left"] = mid
    update_value = {"$set": {'children': parent["children"], 'values': parent["values"]}}
    filter = {"_id": parent["_id"]}
    nodes.update_one(filter, update_value);
    # Delete old node
    nodes.delete_one({"_id": insert_location["_id"]})


def insert_2_node(value, insert_location):
    values = insert_location["values"]
    # Insert value into node in sorted order
    if (values["left"] < value):
        values["right"] = value
    else:
        values["right"] = values["left"]
        values["left"] = value
    # push update to DB
    update_value = {"$set": {'values': values}}
    filter = {"_id": insert_location["_id"]}
    nodes.update_one(filter, update_value)


def get_node_by_id(node_id):
    node = nodes.find_one({'_id': node_id})
    return node


def print_db():
    print("\nAll records in DB")
    cursor = nodes.find()
    for record in cursor:
        print(record)


def insertmany():
    for i in range(0, 1000):
        insert(random.randint(0, 10000))
    print_db()


def insert_sorted():
    for i in range(0, 100):
        insert(i)
    print_db()
# cProfile.run('insert_sorted()')
