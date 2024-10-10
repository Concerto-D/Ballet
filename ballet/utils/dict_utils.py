from typing import TypeVar

A = TypeVar('A')
B = TypeVar('B')

def sum_dicts(dict1, dict2):
    result = dict1.copy()
    result.update(dict2)
    return result

def reverse_dict(d: dict[A, list[B]]) -> dict[B, list[A]]:
    res = {}
    for key, value_list in d.items():
        for value in value_list:
            if value not in res:
                res[value] = []
            res[value].append(key)
    return res

def min_max_set_size_with_keys(my_dict):
    # Get the sizes and the corresponding keys of all sets in the dictionary
    set_sizes = {key: len(s) for key, s in my_dict.items()}
    min_key = min(set_sizes, key=set_sizes.get)
    min_size = set_sizes[min_key]
    max_key = max(set_sizes, key=set_sizes.get)
    max_size = set_sizes[max_key]
    return (min_key, min_size), (max_key, max_size)