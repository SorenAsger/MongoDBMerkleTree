import DBInterface
import DBManagement


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

    def is_2_node(self):
        return self.right is None

    def update(self, db: DBInterface.DatabaseInterface):
        # TODO: updates hash
        pass

    def get_values(self):
        return [self.left, self.right]

    def __eq__(self, other: 'Two3Node'):
        return self.node_id == other.node_id
