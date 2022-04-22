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

    def update_23_node_value_children(self, cache, values, children=None):
        if values[1] is not None:
            values.sort()
        if children is None:
            children = [None, None, None]
        node = self.make_23_node(values, children)
        node.update_hash(cache)
        return node

    def make_23_node(self, values, children):
        node = Two3Node(self.node_id, values[0])
        node.parent = self.parent
        node.right = values[1]
        node.left_child_id = children[0]
        node.mid_child_id = children[1]
        node.right_child_id = children[2]
        return node

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

    def get_proof_values_and_hashes(self, cache, calling_child_id):
        # Omit the calling childs ID
        # We do not need it as the verifier
        # Calculates this hash himself.
        result = [self.get_values()]
        if calling_child_id == self.left_child_id:
            result.append("caller")
        else:
            result.append(get_hash_from_node(self.left_child_id, cache))

        if calling_child_id == self.mid_child_id:
            result.append("caller")
        else:
            result.append(get_hash_from_node(self.mid_child_id, cache))

        if calling_child_id == self.right_child_id:
            result.append("caller")
        else:
            result.append(get_hash_from_node(self.right_child_id, cache))

        return result

    def update_hash(self, cache):
        self.hash_function.update(self.left)
        if not self.is_2_node():
            self.hash_function.update(self.right)
        child_ids = self.get_child_ids()
        hashes = get_hashes_from_nodes(child_ids, cache)
        self.hash_function.update(hashes[0])
        self.hash_function.update(hashes[1])
        self.hash_function.update(hashes[2])
        self.hash = self.hash_function.digest()
        return self

    def get_child_ids(self):
        return [self.left_child_id, self.mid_child_id, self.right_child_id]

    def update_23_node_value_children(self, cache, values, children=None):
        if values[1] is not None:
            values.sort()
        self.left = values[0]
        self.right = values[1]
        if children is not None:
            self.left_child_id = children[0]
            self.mid_child_id = children[1]
            self.right_child_id = children[2]
        self.update_hash(cache)
        return self

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


def get_hash_from_node(child_id, cache) -> bytes:
    if child_id is not None:
        return cache.get(child_id).hash
    return None


def get_hashes_from_nodes(ids, cache):
    assert len(ids) == 3
    if ids[0] is None:
        return [None, None, None]
    if ids[1] is None:
        hashes = [cache.get(ids[0]).hash, None, cache.get(ids[2]).hash]
    else:
        hashes = [cache.get(id).hash for id in ids]
    return hashes