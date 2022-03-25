import hashlib

import DBInterface


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
        self.left = left
        self.node_id = node_id
        self.right = None
        self.left_child_id = None
        self.right_child_id = None
        self.mid_child_id = None
        self.hash = None

    def is_2_node(self):
        return self.right is None

    def update(self, db: DBInterface.Database23NodeInterface):
        m = hashlib.sha256()
        m.update(get_child_hash(self.left_child_id, db))
        m.update(get_value_hash(self.left))
        m.update(get_child_hash(self.mid_child_id, db))
        m.update(get_value_hash(self.right))
        m.update(get_child_hash(self.right_child_id, db))
        self.hash = m.digest()
        # TODO update hash value in database
        pass

    def get_values(self):
        return [self.left, self.right]

    def __eq__(self, other: 'Two3Node'):
        return self.node_id == other.node_id


def get_child_hash(child_id, db: DBInterface.Database23NodeInterface) -> bytes:
    if child_id is not None:
        return db.get_23_node_by_id(child_id).hash
    else:
        raise NotImplementedError()


def get_value_hash(value) -> bytes:
    if value is not None:
        raise NotImplementedError()
    else:
        raise NotImplementedError()
