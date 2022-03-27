from DBInterface import Database23NodeInterface
from DBManagement import MongoDB
from Node import Two3Node


class auth_db_server:

    def __init__(self, dbi=None):
        print("Server started.")
        self.root_id = "root"
        self.dbi = MongoDB()

    def split_node(self, node, value, left_children=None, right_children=None):
        values = [node.left, node.right, value]
        values.sort()
        min_node = self.dbi.create_23_node(values[0], left_children)
        max_node = self.dbi.create_23_node(values[2], right_children)
        return min_node, max_node, values[1]

    def find_nearest_node_and_parent(self, value):
        current = self.dbi.get_23_node_by_id(self.root_id)
        parent = None
        nearest_node = None
        depth = 0
        path = []
        while current is not None:
            current.parent = parent
            path.append(current)
            depth += 1
            # If the value is in the current node
            if value in current.get_values():
                return current, nearest_node
            # 2-node
            if current.is_2_node():
                if value < current.left:
                    child_id = current.left_child_id
                else:
                    child_id = current.right_child_id
            # 3-node
            else:
                if value < current.left:
                    child_id = current.left_child_id
                elif value > current.right:
                    # not super pretty, maybe abstract away into a method of Node?
                    # Have it return the correct child id
                    child_id = current.right_child_id
                else:
                    child_id = current.mid_child_id
            parent = nearest_node
            nearest_node = current
            current = self.dbi.get_23_node_by_id(child_id)

        print("depth of lookup: " + str(depth) + " for value: " + str(value))
        return nearest_node, parent

    def insert(self, value):
        insertion_node, parent = self.find_nearest_node_and_parent(value)
        if insertion_node is not None and value in [insertion_node.left, insertion_node.right]:
            print("value " + str(value) + " is already in the tree.")
        elif insertion_node is None:
            self.insert_empty_tree(value)
        elif insertion_node.is_2_node():
            self.insert_2_node(value, insertion_node)
        elif parent is None:
            self.insert_3_node_root(value, insertion_node)
        elif parent.is_2_node():
            self.insert_3_node_2_parent(value, insertion_node, parent)
        else:
            self.insert_3_node_3_parent(value, insertion_node, parent)

    def insert_3_node_root(self, value, insert_location: 'Two3Node'):
        # TODO Split here
        min_node, max_node, mid = self.split_node(insert_location, value)

        insert_location.left_child_id = min_node.node_id
        insert_location.right_child_id = max_node.node_id
        insert_location.left = mid
        insert_location.right = None

        # TODO: Update parent in database and delete insert_location from database
        # TODO: Could maybe be more efficient to not delete insert_location and reuse it instead?
        # TODO: Update upwards and hash thing
        self.dbi.update_23_node(insert_location)

    def insert_empty_tree(self, value):
        self.dbi.create_root(value)

    def insert_3_node_3_parent(self, value, insert_location: 'Two3Node', parent: 'Two3Node'):
        min_node, max_node, mid = self.split_node(insert_location, value)

        # Now we need to reconstruct pointers from parent min and parent max to the children
        left_child = self.dbi.get_23_node_by_id(parent.left_child_id)
        mid_child = self.dbi.get_23_node_by_id(parent.mid_child_id)
        right_child = self.dbi.get_23_node_by_id(parent.right_child_id)

        all_children = [left_child, mid_child, right_child, min_node, max_node]
        # all_children contains the previous children (left, mid, right) and the new nodes (min and max)
        # We now remove the node that was split and replaced with min and max
        all_children = [child for child in all_children if child != insert_location]
        all_children.sort(key=lambda x: x.left)
        all_children_id = [child.node_id for child in all_children]

        parent_min, parent_max, mid = self.split_node(parent, mid, left_children=all_children_id[:2],
                                                      right_children=all_children_id[2:])
        parent.left_child_id = parent_min.node_id
        parent.right_child_id = parent_max.node_id
        parent.mid_child_id = None
        self.dbi.update_23_node(parent)
        self.dbi.remove_23_node(insert_location)
        # TODO: Update parent in database and delete insert_location from database
        # TODO: Could maybe be more efficient to not delete insert_location and reuse it instead?
        # TODO: Update upwards and hash thing

    def insert_3_node_2_parent(self, value, insert_location: 'Two3Node', parent: 'Two3Node'):
        # Create 2 new nodes for min and max
        min_node, max_node, mid = self.split_node(insert_location, value)

        parent.left_child_id = min_node.node_id
        parent.right_child_id = max_node.node_id
        parent.mid_child_id = None

        if mid > parent.left:
            parent.right = mid
        else:
            parent.right = parent.left
            parent.left = mid
        # TODO: Update parent in database and delete insert_location from database
        # TODO: Could maybe be more efficient to not delete insert_location and reuse it instead?
        # TODO: Update upwards and hash thing
        self.dbi.update_23_node(parent)
        self.dbi.remove_23_node(insert_location)

    def insert_2_node(self, value, insert_location):
        # Insert value into node in sorted order
        if value > insert_location.left:
            insert_location.right = value
        else:
            insert_location.right = insert_location.left
            insert_location.left = value
        # push update to DB
        self.dbi.update_23_node(insert_location)
        # TODO: Update upwards and hash thing

    def print_db(self):
        print("\nAll records in DB")
        cursor = self.dbi.nodes.find()
        for record in cursor:
            print(record)
