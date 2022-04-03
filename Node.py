import DBInterface
from cryptoUtil import HashFunction


class Node:
    def __init__(self, node_id, values, children_ids):
        self.node_id = node_id
        self.values = values
        self.children_ids = children_ids
        self.left_value = values[0]
        if len(values) == 1:
            self.right_value = None
        else:
            self.right_value = values[1]

    def get_values(self):
        return self.values

    def get_children_ids(self):
        return self.children_ids

    def is_2_node(self):
        return len(self.values) == 1


class Two3Node:
    def __init__(self, node_id, left):
        self.hash_function = HashFunction()
        self.left = left
        self.node_id = node_id
        self.right = None
        self.left_child_id = None
        self.right_child_id = None
        self.mid_child_id = None
        self.hash = None
        self.parent = None
        self.child_hashes = []

    def is_2_node(self):
        return self.right is None

    def update(self, db: DBInterface.Database23NodeInterface):
        self.hash_function.update(get_hash_from_node(self.left_child_id, db))
        self.hash_function.update(self.left)
        self.hash_function.update(get_hash_from_node(self.mid_child_id, db))
        if not self.is_2_node():
            self.hash_function.update(self.right)
        self.hash_function.update(self.right)
        self.hash_function.update(get_hash_from_node(self.right_child_id, db))
        self.hash = self.hash_function.digest()
        db.update_23_node(self)

    def get_values(self):
        return [self.left, self.right]

    def get_children_ids(self):
        return [self.left_child_id, self.mid_child_id, self.right_child_id]

    def __eq__(self, other: 'Two3Node'):
        return other is not None and self.node_id == other.node_id

    def __str__(self):
        return f"ID: {self.node_id}, Children ids {self.left_child_id}, {self.mid_child_id}, {self.right_child_id}, " \
               f"Values {self.left}, {self.right}"


def get_hash_from_node(child_id, db: DBInterface.Database23NodeInterface) -> bytes:
    if child_id is not None:
        return db.get_23_node_by_id(child_id).hash
    else:
        return None
