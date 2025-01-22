import numpy as np
from py_structs import to_structs

def load(filename):
    return to_structs(np.load(filename, allow_pickle=True).item())


def flatten_trees(trees):
    return [part for tree in trees for part in flatten_parts(tree.parts)]

def flatten_parts(part_root):   
    parts = []

    def flatten(part):
        parts.append(part)
        for child in part.children:
            flatten(child)
    
    flatten(part_root)
    return parts

def parts_map(part_root):
    parts = {}

    def flatten(part):
        parts[part.name] = part
        for child in part.children:
            flatten(child)
    
    flatten(part_root)
    return parts    



def class_counts(part, counts=None):
    counts = counts or {}
    name = part.class_name

    if name not in counts:
        counts[name] = 1
    else:
        counts[name] += 1

    for child in part.children:
        class_counts(child, counts)

    return counts



def get_parts(part_root, class_names, self_recursive=False):
    parts = []

    def recurse(part):
        matches = part.class_name in class_names
        if matches:
            parts.append(part)
        if self_recursive or (not matches):
            for child in part.children:
                recurse(child)


    recurse(part_root)
    return parts

def get_parts_parent(part_root, class_names, self_recursive=False):
    parts = []

    def recurse(parent, part):
        matches = part.class_name in class_names
        if matches:
            parts.append((parent, part))
        if self_recursive or (not matches):
            for child in part.children:
                recurse(part, child)


    recurse(None, part_root)
    return parts
