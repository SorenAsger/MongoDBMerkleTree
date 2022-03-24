import random

from pymongo import MongoClient
import cProfile

from DBManagement import MongoDB

# client = MongoClient('localhost', 27017)
# db = client.test_database
# nodes = db.nodes
root_id = "root"

dbi = MongoDB()


def split_node(node, value, left_children=None, right_children=None):
    values = [node.left, node.right, value]
    values.sort()
    min_node = dbi.create_23_node(values[0], left_children)
    max_node = dbi.create_23_node(values[2], right_children)
    return min_node, max_node, values[1]


def find_nearest_node_and_parent(value):
    current = dbi.get_23_node_by_id(root_id)
    parent = None
    nearest_node = None
    depth = 0
    while current is not None:
        depth += 1
        # If the value is in the current node
        if value in current.get_values():
            return current, nearest_node
        # 2-node
        if current.is_2_node():
            if value < current.left_value:
                child_id = current.left_child_id
            else:
                child_id = current.right_child_id
        # 3-node
        else:
            if value < current.left_value:
                child_id = current.left_child_id
            elif value > current.right_value:
                # not super pretty, maybe abstract away into a method of Node?
                # Have it return the correct child id
                child_id = current.right_child_id
            else:
                child_id = current.mid_child_id
        parent = nearest_node
        nearest_node = current
        current = dbi.get_23_node_by_id(child_id)
    print("depth of lookup: " + str(depth) + " for value: " + str(value))
    return nearest_node, parent


def insert(value):
    insertion_node, parent = find_nearest_node_and_parent(value)
    if insertion_node is not None and value in insertion_node:
        print("value " + str(value) + " is already in the tree.")
    elif insertion_node is None:
        insert_empty_tree(value)
    elif insertion_node.is_2_node():
        insert_2_node(value, insertion_node)
    elif parent is None:
        insert_3_node_root(value, insertion_node)
    elif parent.is_2_node():
        insert_3_node_2_parent(value, insertion_node, parent)
    else:
        insert_3_node_3_parent(value, insertion_node, parent)


def insert_3_node_root(value, insert_location):
    # TODO Split here
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


def insert_3_node_3_parent(value, insert_location: 'Two3Node', parent: 'Two3Node'):
    min_node, max_node, mid = split_node(insert_location, value)

    # Now we need to reconstruct pointers from parent min and parent max to the children
    left_child = dbi.get_23_node_by_id(parent.left_child_id)
    mid_child = dbi.get_23_node_by_id(parent.mid_child_id)
    right_child = dbi.get_23_node_by_id(parent.right_child_id)

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
