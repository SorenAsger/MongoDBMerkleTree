from typing import List

from DBInterface import Database23NodeInterface
from Node import Two3Node


class auth_db_server:

    def __init__(self, dbi: Database23NodeInterface):
        print("Server started.")
        self.root_id = None
        self.dbi = dbi

    def split_node(self, node, value, left_children=None, right_children=None):
        values = [node.left, node.right, value]
        values.sort()
        min_node = self.dbi.create_23_node(values[0], left_children)
        max_node = self.dbi.create_23_node(values[2], right_children)
        min_node.update_hash(self.dbi)
        max_node.update_hash(self.dbi)
        return min_node, max_node, values[1]

    def find_nearest_node_and_parent(self, value):
        current = self.dbi.get_23_node_by_id(self.root_id)
        parent = None
        nearest_node = None
        depth = 0
        path = []
        while current is not None:
            current.parent = nearest_node
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

        #print("depth of lookup: " + str(depth) + " for value: " + str(value))
        return nearest_node, parent

    def insert(self, value):
        if self.root_id is None:
            self.root_id = "root"
            self.dbi.create_root(value, self.root_id)
            return
        insertion_node, parent = self.find_nearest_node_and_parent(value)
        insertion_node.parent = parent
        self.insert_at(insertion_node, value)

    def update_hashes_upwards(self, starting_node: 'Two3Node'):
        current = starting_node
        while current is not None:
            current.update_hash(self.dbi)
            current = current.parent

    def insert_at(self, insertion_node: 'Two3Node', value):
        parent = insertion_node.parent
        if insertion_node is not None and value in [insertion_node.left, insertion_node.right]:
            print("value " + str(value) + " is already in the tree.")
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
        #print("Rootinsert", insert_location.node_id)
        min_node, max_node, mid = self.split_node(insert_location, value)

        insert_location.left_child_id = min_node.node_id
        insert_location.right_child_id = max_node.node_id
        insert_location.left = mid
        insert_location.right = None

        # TODO: Update parent in database and delete insert_location from database
        # TODO: Could maybe be more efficient to not delete insert_location and reuse it instead?
        # TODO: Update upwards and hash thing
        self.dbi.update_23_node(insert_location)
        insert_location.update_hash(self.dbi)

    def insert_3_node_3_parent(self, value, insert_location: 'Two3Node', parent: 'Two3Node'):
        min_node, max_node, mid = self.split_node(insert_location, value)

        # Now we need to reconstruct pointers from parent min and parent max to the children
        #print("3_n_3")
        #print(parent)
        #print([parent.left_child_id, parent.mid_child_id, parent.right_child_id])
        #print([parent.left, parent.right])

        if insert_location.node_id == parent.left_child_id:
            all_children_id = [min_node.node_id, max_node.node_id, parent.mid_child_id, parent.right_child_id]
        elif insert_location.node_id == parent.mid_child_id:
            all_children_id = [parent.left_child_id, min_node.node_id, max_node.node_id, parent.right_child_id]
        else:
            all_children_id = [parent.left_child_id, parent.mid_child_id, min_node.node_id, max_node.node_id]
        values = sorted([parent.left, parent.right, mid])
        self.insert_3_node_help(parent, all_children_id, values)
        self.dbi.update_23_node(parent)
        self.dbi.remove_23_node(insert_location)
        # TODO: Update parent in database and delete insert_location from database
        # TODO: Could maybe be more efficient to not delete insert_location and reuse it instead?
        # TODO: Update upwards and hash thing

    def insert_3_node_help(self, node: "Two3Node", children_ids, values):
        # Children ids are sorted
        parent = node.parent
        min_node = self.dbi.create_23_node(values[0], children_ids[:2])
        min_node.update_hash(self.dbi)
        max_node = self.dbi.create_23_node(values[2], children_ids[2:])
        max_node.update_hash(self.dbi)

        if parent is None:
            # Handle case for root
            node.left_child_id = min_node.node_id
            node.right_child_id = max_node.node_id
            node.left = values[1]
            node.right = None
            node.mid_child_id = None
            self.dbi.update_23_node(node)
            self.update_hashes_upwards(node)
            # ROOT CASE SHOULD WORK
        elif parent.is_2_node():
            if node.node_id == parent.left_child_id:
                parent.left_child_id = min_node.node_id
                parent.mid_child_id = max_node.node_id
            else:
                parent.mid_child_id = min_node.node_id
                parent.right_child_id = max_node.node_id
            if values[1] > parent.left:
                parent.right = values[1]
            else:
                parent.right = parent.left
                parent.left = values[1]
            self.dbi.update_23_node(parent)
            self.dbi.remove_23_node(node)
            self.update_hashes_upwards(parent)

        else:
            # Parent is 3 node as well
            # Need to create a new temp 4 node
            new_values = sorted([parent.left, parent.right, values[1]])
            if node.node_id == parent.left_child_id:
                new_children_id = [min_node.node_id, max_node.node_id, parent.mid_child_id, parent.right_child_id]
            elif node.node_id == parent.mid_child_id:
                new_children_id = [parent.left_child_id, min_node.node_id, max_node.node_id, parent.right_child_id]
            else:
                new_children_id = [parent.left_child_id, parent.mid_child_id, min_node.node_id, max_node.node_id]
            self.insert_3_node_help(parent, new_children_id, new_values)
            self.dbi.remove_23_node(node)

    def insert_3_node_2_parent(self, value, insert_location: 'Two3Node', parent: 'Two3Node'):
        # Create 2 new nodes for min and max
        min_node, max_node, mid = self.split_node(insert_location, value)

        if insert_location.node_id == parent.left_child_id:
            parent.left_child_id = min_node.node_id
            parent.mid_child_id = max_node.node_id
        else:
            parent.mid_child_id = min_node.node_id
            parent.right_child_id = max_node.node_id

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
        self.update_hashes_upwards(parent)

    def insert_2_node(self, value, insert_location):
        # Insert value into node in sorted order
        if value > insert_location.left:
            insert_location.right = value
        else:
            insert_location.right = insert_location.left
            insert_location.left = value
        # push update to DB
        self.dbi.update_23_node(insert_location)
        self.update_hashes_upwards(insert_location)

    def print_db(self):
        print("\nAll records in DB")
        cursor = self.dbi.nodes.find()
        for record in cursor:
            print(record)

    def destroy_db(self):
        self.dbi.destroy_db()

    def tree_to_str(self, node: 'Two3Node', depth=0):
        if node is None:
            return "None"
        left = self.tree_to_str(self.dbi.get_23_node_by_id(node.left_child_id), depth + 1)
        mid = self.tree_to_str(self.dbi.get_23_node_by_id(node.mid_child_id), depth + 1)
        right = self.tree_to_str(self.dbi.get_23_node_by_id(node.right_child_id), depth + 1)
        tabs = "\t" * depth
        return f"Depth {depth} " + node.__str__() + f"\n {tabs} | {left} \n {tabs} | {mid} \n {tabs} | {right}"

    def print_tree(self):
        print(self.tree_to_str(self.dbi.get_23_node_by_id(self.root_id)))
