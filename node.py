from crypto_util import HashFunction


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


class HoleNode:
    def __init__(self, node, child):
        self.node_id = node.node_id
        self.parent = node.parent
        self.left_child_id = child

    def is_2_node(self):
        return True

    def is_hole_node(self):
        return True


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

    def is_leaf(self):
        return self.left_child_id is None

    def get_proof_values_and_hashes(self, db, calling_child_id):
        # Omit the calling childs ID
        # We do not need it as the verifier
        # Calculates this hash himself.
        result = [self.get_values()]
        if calling_child_id == self.left_child_id:
            result.append("caller")
        else:
            result.append(get_hash_from_node(self.left_child_id, db))

        if calling_child_id == self.mid_child_id:
            result.append("caller")
        else:
            result.append(get_hash_from_node(self.mid_child_id, db))

        if calling_child_id == self.right_child_id:
            result.append("caller")
        else:
            result.append(get_hash_from_node(self.right_child_id, db))

        return result

    def update_hash(self, db):
        self.hash_function.update(self.left)
        if not self.is_2_node():
            self.hash_function.update(self.right)
        self.hash_function.update(get_hash_from_node(self.left_child_id, db))
        self.hash_function.update(get_hash_from_node(self.mid_child_id, db))
        self.hash_function.update(get_hash_from_node(self.right_child_id, db))
        self.hash = self.hash_function.digest()
        db.update_23_node(self)

    def get_values(self):
        return [self.left, self.right]

    def get_children_ids(self):
        return [self.left_child_id, self.mid_child_id, self.right_child_id]

    def get_sibling(self, node):
        if self.is_2_node():
            if self.left_child_id == node.node_id:
                return self.right_child_id
            else:
                return self.left_child_id
        else:
            if self.left_child_id == node.node_id or self.right_child_id == node.node_id:
                return self.mid_child_id
            else:
                return self.left_child_id

    def is_hole_node(self):
        return False

    def __eq__(self, other: 'Two3Node'):
        return other is not None and self.node_id == other.node_id

    def __str__(self):
        return f"ID: {self.node_id}, Children ids {self.left_child_id}, {self.mid_child_id}, {self.right_child_id}, " \
               f"Values {self.left}, {self.right}"


def get_hash_from_node(child_id, db) -> bytes:
    if child_id is not None:
        return db.get_23_node_by_id(child_id).hash
    return None
